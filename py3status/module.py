import os
import imp
import inspect

from threading import Thread, Timer
from collections import OrderedDict
from time import time

from py3status.py3 import Py3, PY3_CACHE_FOREVER
from py3status.profiling import profile


class Module(Thread):
    """
    This class represents a user module (imported file).
    It is responsible for executing it every given interval and
    caching its output based on user will.
    """

    PARAMS_NEW = 'new'
    PARAMS_LEGACY = 'legacy'

    def __init__(self, module, user_modules, py3_wrapper):
        """
        We need quite some stuff to occupy ourselves don't we ?
        """
        Thread.__init__(self)
        self.cache_time = None
        self.click_events = False
        self.config = py3_wrapper.config
        self.has_post_config_hook = False
        self.has_kill = False
        self.i3status_thread = py3_wrapper.i3status_thread
        self.last_output = []
        self.lock = py3_wrapper.lock
        self.methods = OrderedDict()
        self.module_class = None
        self.module_full_name = module
        self.module_inst = ''.join(module.split(' ')[1:])
        self.module_name = module.split(' ')[0]
        self.new_update = False
        self.nagged = False
        self.prevent_refresh = False
        self.sleeping = False
        self.timer = None

        # py3wrapper this is private and any modules accessing their instance
        # should only use it on the understanding that it is not supported.
        self._py3_wrapper = py3_wrapper
        #
        self.set_module_options(module)
        self.load_methods(module, user_modules)

    def __repr__(self):
        return '<Module {}>'.format(self.module_full_name)

    @staticmethod
    def load_from_file(filepath):
        """
        Return user-written class object from given path.
        """
        class_inst = None
        expected_class = 'Py3status'
        module_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        if file_ext.lower() == '.py':
            py_mod = imp.load_source(module_name, filepath)
            if hasattr(py_mod, expected_class):
                class_inst = py_mod.Py3status()
        return class_inst

    @staticmethod
    def load_from_namespace(module_name):
        """
        Load a py3status bundled module.
        """
        class_inst = None
        name = 'py3status.modules.{}'.format(module_name)
        py_mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            py_mod = getattr(py_mod, comp)
        class_inst = py_mod.Py3status()
        return class_inst

    def start_module(self):
        """
        Start the module running.
        """
        # Modules can define a post_config_hook() method which will be run
        # after the module has had it config settings applied and before it has
        # its main method(s) called for the first time.  This allows modules to
        # perform any necessary setup.
        if self.has_post_config_hook:
            self.module_class.post_config_hook()
        # Start the module and call its output method(s)
        self.start()

    def force_update(self):
        """
        Forces an update of the module.
        """
        # clear cached_until for each method to allow update
        for meth in self.methods:
            self.methods[meth]['cached_until'] = time()
            if self.config['debug']:
                self._py3_wrapper.log('clearing cache for method {}'.format(meth))
        # cancel any existing timer
        if self.timer:
            self.timer.cancel()
        # get the thread to update itself
        self.timer = Timer(0, self.run)
        self.timer.start()

    def sleep(self):
        self.sleeping = True
        # cancel any existing timer
        if self.timer:
            self.timer.cancel()

    def wake(self):
        self.sleeping = False
        if self.cache_time is None:
            return
        # new style modules can signal they want to cache forever
        if self.cache_time == PY3_CACHE_FOREVER:
            return
        # restart
        delay = max(self.cache_time - time(), 0)
        self.timer = Timer(delay, self.run)
        self.timer.start()

    def set_updated(self):
        """
        Mark the module as updated.
        We check if the actual content has changed and if so we trigger an
        update in py3status.
        """
        # get latest output
        output = []
        for method in self.methods.values():
            data = method['last_output']
            if isinstance(data, list):
                output.extend(data)
            else:
                output.append(data)
        # if changed store and force display update.
        if output != self.last_output:
            self.last_output = output
            self._py3_wrapper.notify_update(self.module_full_name)

    def get_latest(self):
        """
        return latest output.
        """
        return self.last_output

    def set_module_options(self, module):
        """
        Set universal module options to be interpreted by i3bar
        https://i3wm.org/i3status/manpage.html#_universal_module_options
        """
        self.module_options = {}
        mod_config = self.i3status_thread.config.get(module, {})

        if 'min_width' in mod_config:
            self.module_options['min_width'] = mod_config['min_width']

        if 'separator' in mod_config:
            separator = mod_config['separator']
            if not isinstance(separator, bool):
                err = 'invalid "separator" attribute, should be a bool'
                raise TypeError(err)

            self.module_options['separator'] = separator

        if 'separator_block_width' in mod_config:
            sep_block_width = mod_config['separator_block_width']
            if not isinstance(sep_block_width, int):
                err = 'invalid "separator_block_width" attribute, '
                err += "should be an int"
                raise TypeError(err)

            self.module_options['separator_block_width'] = sep_block_width

        if 'align' in mod_config:
            align = mod_config['align']
            if not (isinstance(align, str) and
                    align.lower() in ("left", "center", "right")):
                err = 'invalid "align" attribute, valid values are:'
                err += ' left, center, right'
                raise ValueError(err)

            self.module_options['align'] = align

    def process_composite(self, response):
        """
        Process a composite response.
        composites do not have inter item separators as they appear joined.
        We need to respect the universal options too.
        """
        composite = response['composite']
        if not isinstance(composite, list):
            raise Exception('expecting "composite" key in response')
        # if list is empty nothing to do
        if not len(composite):
            return
        if 'full_text' in response:
            err = 'conflicting "full_text" and "composite" in response'
            raise Exception(err)
        # set universal options on last component
        composite[-1].update(self.module_options)
        # calculate any min width (we split this across components)
        min_width = None
        if 'min_width' in self.module_options:
            min_width = int(self.module_options['min_width'] / len(composite))
        # store alignment
        align = None
        if 'align' in self.module_options:
            align = self.module_options['align']

        # update all components
        color = response.get('color')
        for index, item in enumerate(response['composite']):
            # validate the response
            if 'full_text' not in item:
                raise KeyError('missing "full_text" key in response')
            # make sure all components have a name
            if 'name' not in item:
                instance_index = item.get('index', index)
                item['instance'] = '{} {}'.format(
                    self.module_inst, instance_index
                )
                item['name'] = self.module_name
            # hide separator for all inner components unless existing
            if index != len(response['composite']) - 1:
                if 'separator' not in item:
                    item['separator'] = False
                    item['separator_block_width'] = 0
            # set min width
            if min_width:
                item['min_width'] = min_width
            # set align
            if align:
                item['align'] = align
            # If a color was supplied for the composite and a composite
            # part does not supply a color, use the composite color.
            if color and 'color' not in item:
                item['color'] = color

    def _params_type(self, method_name, instance):
        """
        Check to see if this is a legacy method or shiny new one

        legacy update method:
            def update(self, i3s_output_list, i3s_config):
                ...

        new update method:
            def update(self):
                ...

        Returns False if the method does not exist,
        else PARAMS_NEW or PARAMS_LEGACY
        """

        method = getattr(instance, method_name, None)
        if not method:
            return False

        # Check the parameters we simply count the number of args and don't
        # allow any extras like keywords.
        arg_count = 1
        # on_click method has extra events parameter
        if method_name == 'on_click':
            arg_count = 2
        args, vargs, kw, defaults = inspect.getargspec(method)
        if len(args) == arg_count and not vargs and not kw:
            return self.PARAMS_NEW
        else:
            return self.PARAMS_LEGACY

    def load_methods(self, module, user_modules):
        """
        Read the given user-written py3status class file and store its methods.
        Those methods will be executed, so we will deliberately ignore:
            - private methods starting with _
            - decorated methods such as @property or @staticmethod
            - 'on_click' methods as they'll be called upon a click_event
            - 'kill' methods as they'll be called upon this thread's exit
        """
        # user provided modules take precedence over py3status provided modules
        if self.module_name in user_modules:
            include_path, f_name = user_modules[self.module_name]
            self._py3_wrapper.log(
                'loading module "{}" from {}{}'.format(module, include_path,
                                                       f_name))
            class_inst = self.load_from_file(include_path + f_name)
        # load from py3status provided modules
        else:
            self._py3_wrapper.log(
                'loading module "{}" from py3status.modules.{}'.format(
                    module, self.module_name))
            class_inst = self.load_from_namespace(self.module_name)

        if class_inst:
            self.module_class = class_inst
            try:
                # containers have items attribute set to a list of contained
                # module instance names.  If there are no contained items then
                # ensure that we have a empty list.
                if class_inst.Meta.container:
                    class_inst.items = []
            except AttributeError:
                pass

            # apply module configuration from i3status config
            mod_config = self.i3status_thread.config.get(module, {})
            for config, value in mod_config.items():
                # names starting with '.' are private
                if not config.startswith('.'):
                    setattr(self.module_class, config, value)

            # Add the py3 module helper if modules self.py3 is not defined
            if not hasattr(self.module_class, 'py3'):
                setattr(self.module_class, 'py3', Py3(self))

            # get the available methods for execution
            for method in sorted(dir(class_inst)):
                if method.startswith('_'):
                    continue
                else:
                    m_type = type(getattr(class_inst, method))
                    if 'method' in str(m_type):
                        params_type = self._params_type(method, class_inst)
                        if method == 'on_click':
                            self.click_events = params_type
                        elif method == 'kill':
                            self.has_kill = params_type
                        elif method == 'post_config_hook':
                            self.has_post_config_hook = True
                        else:
                            # the method_obj stores infos about each method
                            # of this module.
                            method_obj = {
                                'cached_until': time(),
                                'call_type': params_type,
                                'instance': None,
                                'last_output': {
                                    'name': method,
                                    'full_text': ''
                                },
                                'method': method,
                                'name': None
                            }
                            self.methods[method] = method_obj

        # done, log some debug info
        if self.config['debug']:
            self._py3_wrapper.log(
                'module "{}" click_events={} has_kill={} methods={}'.format(
                    module, self.click_events, self.has_kill,
                    self.methods.keys()))

    def click_event(self, event):
        """
        Execute the 'on_click' method of this module with the given event.
        """
        # we can prevent request that a refresh after the event has happened
        # by setting this to True.  Modules should do this via
        # py3.prevent_refresh()
        self.prevent_refresh = False
        try:
            click_method = getattr(self.module_class, 'on_click')
            if self.click_events == self.PARAMS_NEW:
                # new style modules
                click_method(event)
            else:
                # legacy modules had extra parameters passed
                click_method(self.i3status_thread.json_list,
                             self.i3status_thread.config['general'], event)
            self.set_updated()
        except Exception:
            msg = 'on_click event in `{}` failed'.format(self.module_full_name)
            self._py3_wrapper.report_exception(msg)

    @profile
    def run(self):
        """
        On a timely fashion, execute every method found for this module.
        We will respect and set a cache timeout for each method if the user
        didn't already do so.
        We will execute the 'kill' method of the module when we terminate.
        """
        # cancel any existing timer
        if self.timer:
            self.timer.cancel()

        if self.lock.is_set():
            cache_time = None
            # execute each method of this module
            for meth, obj in self.methods.items():
                my_method = self.methods[meth]

                # always check the lock
                if not self.lock.is_set():
                    break

                # respect the cache set for this method
                if time() < obj['cached_until']:
                    if not cache_time or obj['cached_until'] < cache_time:
                        cache_time = obj['cached_until']
                    continue

                try:
                    # execute method and get its output
                    method = getattr(self.module_class, meth)
                    if my_method['call_type'] == self.PARAMS_NEW:
                        # new style modules
                        response = method()
                    else:
                        # legacy modules had parameters passed
                        response = method(
                            self.i3status_thread.json_list,
                            self.i3status_thread.config['general'])

                    if isinstance(response, dict):
                        # this is a shiny new module giving a dict response
                        result = response
                    elif isinstance(response, tuple):
                        # this is an old school module reporting its position
                        position, result = response
                        if not isinstance(result, dict):
                            raise TypeError('response should be a dict')
                    else:
                        raise TypeError('response should be a dict')

                    if 'composite' in response:
                        self.process_composite(response)
                    else:
                        # validate the response
                        if 'full_text' not in result:
                            try:
                                # try to set the full_text automatically
                                full_text = self.module_class.py3.safe_format()
                                result['full_text'] = full_text
                            except:
                                err = 'missing "full_text" key in response'
                                raise KeyError(err)
                        # set universal module options in result
                        result.update(self.module_options)

                    result['instance'] = self.module_inst
                    result['name'] = self.module_name

                    # initialize method object
                    if my_method['name'] is None:
                        my_method['name'] = result['name']
                        if 'instance' in result:
                            my_method['instance'] = result['instance']
                        else:
                            my_method['instance'] = result['name']

                    # update method object cache
                    if 'cached_until' in result:
                        cached_until = result['cached_until']
                        # remove this so we can check later for output changes
                        del result['cached_until']
                    else:
                        cached_until = time() + self.config['cache_timeout']
                    my_method['cached_until'] = cached_until
                    if not cache_time or cached_until < cache_time:
                        cache_time = cached_until

                    # update method object output
                    if 'composite' in response:
                        my_method['last_output'] = result['composite']
                    else:
                        my_method['last_output'] = result

                    # mark module as updated
                    self.set_updated()

                    # debug info
                    if self.config['debug']:
                        self._py3_wrapper.log(
                            'method {} returned {} '.format(meth, result))
                except Exception:
                    msg = 'Instance `{}`, user method `{}` failed'
                    msg = msg.format(self.module_full_name, meth)
                    notify = not self.nagged
                    self._py3_wrapper.report_exception(msg, notify_user=notify)
                    self.nagged = True

            if cache_time is None:
                cache_time = time() + self.config['cache_timeout']
            self.cache_time = cache_time
            # new style modules can signal they want to cache forever
            if cache_time == PY3_CACHE_FOREVER:
                return
            # don't be hasty mate
            # set timer to do update next time one is needed
            if not self.sleeping:
                delay = max(cache_time - time(),
                            self.config['minimum_interval'])
                self.timer = Timer(delay, self.run)
                self.timer.start()

    def kill(self):
        # stop timer if exists
        if self.timer:
            self.timer.cancel()
        # check and execute the 'kill' method if present
        if self.has_kill:
            try:
                kill_method = getattr(self.module_class, 'kill')
                if self.has_kill == self.PARAMS_NEW:
                    kill_method()
                else:
                    # legacy call parameters
                    kill_method(self.i3status_thread.json_list,
                                self.i3status_thread.config['general'])
            except Exception:
                # this would be stupid to die on exit
                pass
