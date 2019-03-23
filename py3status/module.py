import os
import imp
import inspect

from collections import OrderedDict
from time import time
from random import randint

from py3status.composite import Composite
from py3status.constants import MARKUP_LANGUAGES, POSITIONS
from py3status.py3 import Py3, PY3_CACHE_FOREVER, ModuleErrorException
from py3status.profiling import profile
from py3status.formatter import Formatter

# basestring does not exist in python3
try:
    basestring
except NameError:
    basestring = str


class Module:
    """
    This class represents a user module (imported file).
    It is responsible for executing it every given interval and
    caching its output based on user will.
    """

    PARAMS_NEW = "new"
    PARAMS_LEGACY = "legacy"

    def __init__(self, module, user_modules, py3_wrapper, instance=None):
        """
        We need quite some stuff to occupy ourselves don't we ?
        """
        self.allow_config_clicks = True
        self.allow_urgent = None
        self.cache_time = None
        self.click_events = False
        self.config = py3_wrapper.config
        self.disabled = False
        self.enabled = False
        self.error_messages = None
        self.error_hide = False
        self.has_post_config_hook = False
        self.has_kill = False
        self.i3status_thread = py3_wrapper.i3status_thread
        self.last_output = []
        self.methods = OrderedDict()
        self.module_class = instance
        self.module_full_name = module
        self.module_inst = "".join(module.split(" ")[1:])
        self.module_name = module.split(" ")[0]
        self.new_update = False
        self.nagged = False
        self.prevent_refresh = False
        self.sleeping = False
        self.terminated = False
        self.testing = self.config.get("testing")
        self.urgent = False
        self.i3bar_gaps_urgent_options = {}

        # create a nice name for the module that matches what the module is
        # called in the user config
        if self.module_inst.startswith("_anon_module_"):
            self.module_nice_name = self.module_name
        else:
            self.module_nice_name = self.module_full_name

        # py3wrapper this is private and any modules accessing their instance
        # should only use it on the understanding that it is not supported.
        self._py3_wrapper = py3_wrapper

        try:
            self.load_methods(module, user_modules)
        except Exception as e:
            # Import failed notify user in module error output
            self.disabled = True
            self.methods["error"] = {}
            self.error_index = 0
            self.error_messages = [
                self.module_nice_name,
                u"{}: Import Error, {}".format(self.module_nice_name, str(e)),
            ]
            self.error_output(self.error_messages[0])
            # log the error
            msg = "Module `{}` could not be loaded".format(self.module_full_name)
            if isinstance(e, SyntaxError):
                # provide full traceback
                self._py3_wrapper.report_exception(msg, notify_user=False)
            else:
                # module import error we can just report the module that cannot
                # be imported
                self._py3_wrapper.log(msg)
                self._py3_wrapper.log(str(e))

        # check module/py3status config section
        if not self.disabled:
            self.set_module_options(module)

    def __repr__(self):
        return "<Module {}>".format(self.module_full_name)

    @staticmethod
    def load_from_file(filepath):
        """
        Return user-written class object from given path.
        """
        class_inst = None
        expected_class = "Py3status"
        module_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        if file_ext.lower() == ".py":
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
        name = "py3status.modules.{}".format(module_name)
        py_mod = __import__(name)
        components = name.split(".")
        for comp in components[1:]:
            py_mod = getattr(py_mod, comp)
        class_inst = py_mod.Py3status()
        return class_inst

    def prepare_module(self):
        """
        Ready the module to get it ready to start.
        """
        # Modules can define a post_config_hook() method which will be run
        # after the module has had it config settings applied and before it has
        # its main method(s) called for the first time.  This allows modules to
        # perform any necessary setup.
        if self.has_post_config_hook:
            try:
                self.module_class.post_config_hook()
            except Exception as e:
                # An exception has been thrown in post_config_hook() disable
                # the module and show error in module output
                self.terminated = True
                self.error_index = 0

                self.error_messages = [
                    self.module_nice_name,
                    u"{}: {}".format(
                        self.module_nice_name, str(e) or e.__class__.__name__
                    ),
                ]
                self.error_output(self.error_messages[0])
                msg = "Exception in `%s` post_config_hook()" % self.module_full_name
                self._py3_wrapper.report_exception(msg, notify_user=False)
                self._py3_wrapper.log("terminating module %s" % self.module_full_name)
        self.enabled = True

    def runtime_error(self, msg, method):
        """
        Show the error in the bar
        """
        if self.testing:
            self._py3_wrapper.report_exception(msg)
            raise KeyboardInterrupt

        if self.error_hide:
            self.hide_errors()
            return

        # only show first line of error
        msg = msg.splitlines()[0]

        errors = [self.module_nice_name, u"{}: {}".format(self.module_nice_name, msg)]

        # if we have shown this error then keep in the same state
        if self.error_messages != errors:
            self.error_messages = errors
            self.error_index = 0
        self.error_output(self.error_messages[self.error_index], method)

    def error_output(self, message, method_affected=None):
        """
        Something is wrong with the module so we want to output the error to
        the i3bar
        """
        color_fn = self._py3_wrapper.get_config_attribute
        color = color_fn(self.module_full_name, "color_error")
        if hasattr(color, "none_setting"):
            color = color_fn(self.module_full_name, "color_bad")
        if hasattr(color, "none_setting"):
            color = None

        error = {
            "full_text": message,
            "color": color,
            "instance": self.module_inst,
            "name": self.module_name,
        }
        for method in self.methods.values():
            if method_affected and method["method"] != method_affected:
                continue

            method["last_output"] = [error]

        self.allow_config_clicks = False
        self.set_updated()

    def hide_errors(self):
        """
        hide the module in the i3bar
        """
        for method in self.methods.values():
            method["last_output"] = {}

        self.allow_config_clicks = False
        self.error_hide = True
        self.set_updated()

    def start_module(self):
        """
        Start the module running.
        """
        self.prepare_module()
        if not (self.disabled or self.terminated):
            # Start the module and call its output method(s)
            self._py3_wrapper.log("starting module %s" % self.module_full_name)
            self._py3_wrapper.timeout_queue_add(self)

    def force_update(self):
        """
        Forces an update of the module.
        """
        if self.disabled or self.terminated or not self.enabled:
            return
        # clear cached_until for each method to allow update
        for meth in self.methods:
            self.methods[meth]["cached_until"] = time()
            if self.config["debug"]:
                self._py3_wrapper.log("clearing cache for method {}".format(meth))
        # set module to update
        self._py3_wrapper.timeout_queue_add(self)

    def sleep(self):
        self.sleeping = True

    def disable_module(self):
        # hide message
        self.disabled = True
        # purge from any container modules
        self._py3_wrapper.purge_module(self.module_full_name)
        self.error_output(u"")
        self._py3_wrapper.log("disabling module `%s`" % self.module_full_name)

    def wake(self):
        self.sleeping = False
        if self.disabled:
            # module is disabled so don't wake
            return
        if self.cache_time is None:
            return
        # new style modules can signal they want to cache forever
        if self.cache_time == PY3_CACHE_FOREVER:
            return
        # restart
        self._py3_wrapper.timeout_queue_add(self, self.cache_time)

    def set_updated(self):
        """
        Mark the module as updated.
        We check if the actual content has changed and if so we trigger an
        update in py3status.
        """
        # get latest output
        output = []
        for method in self.methods.values():
            data = method["last_output"]
            if isinstance(data, list):
                if self.testing and data:
                    data[0]["cached_until"] = method.get("cached_until")
                output.extend(data)
            else:
                # if the output is not 'valid' then don't add it.
                if data.get("full_text") or "separator" in data:
                    if self.testing:
                        data["cached_until"] = method.get("cached_until")
                    output.append(data)
        # if changed store and force display update.
        if output != self.last_output:
            # has the modules output become urgent?
            # we only care the update that this happens
            # not any after then.
            urgent = True in [x.get("urgent") for x in output]
            if urgent != self.urgent:
                self.urgent = urgent
            else:
                urgent = False
            self.last_output = output
            self._py3_wrapper.notify_update(self.module_full_name, urgent)

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
        self.i3bar_module_options = {}
        self.i3bar_gaps_module_options = {}
        self.py3status_module_options = {}
        fn = self._py3_wrapper.get_config_attribute

        def make_quotes(options):
            x = ["`{}`".format(x) for x in options]
            if len(x) > 2:
                x = [", ".join(x[:-1]), x[-1]]
            return " or ".join(x)

        # i3bar
        min_width = fn(self.module_full_name, "min_width")
        if not hasattr(min_width, "none_setting"):
            if not isinstance(min_width, int):
                err = "Invalid `min_width` attribute, should be an int. "
                err += "Got `{}`.".format(min_width)
                raise TypeError(err)
            self.i3bar_module_options["min_width"] = min_width

            align = fn(self.module_full_name, "align")
            if not hasattr(align, "none_setting"):
                if align not in POSITIONS:
                    err = "Invalid `align` attribute, should be "
                    err += make_quotes(POSITIONS)
                    err += ". Got `{}`.".format(align)
                    raise ValueError(err)
                self.i3bar_module_options["align"] = align

        separator = fn(self.module_full_name, "separator")
        if not hasattr(separator, "none_setting"):
            if not isinstance(separator, bool):
                err = "Invalid `separator` attribute, should be a boolean. "
                err += "Got `{}`.".format(separator)
                raise TypeError(err)
            self.i3bar_module_options["separator"] = separator

        separator_block_width = fn(self.module_full_name, "separator_block_width")
        if not hasattr(separator_block_width, "none_setting"):
            if not isinstance(separator_block_width, int):
                err = "Invalid `separator_block_width` attribute, "
                err += "should be an int. "
                err += "Got `{}`.".format(separator_block_width)
                raise TypeError(err)
            self.i3bar_module_options["separator_block_width"] = separator_block_width

        # i3bar_gaps
        background = fn(self.module_full_name, "background")
        if not hasattr(background, "none_setting"):
            color = self.module_class.py3._get_color(background)
            if not color:
                err = "Invalid `background` attribute should be a color. "
                err += "Got `{}`.".format(background)
                raise ValueError(err)
            self.i3bar_gaps_module_options["background"] = color

        border = fn(self.module_full_name, "border")
        if not hasattr(border, "none_setting"):
            color = self.module_class.py3._get_color(border)
            if not color:
                err = "Invalid `border` attribute, should be a color. "
                err += "Got `{}`.".format(border)
                raise ValueError(err)
            self.i3bar_gaps_module_options["border"] = color

            borders = ["top", "right", "bottom", "left"]
            for name in ["border_" + x for x in borders]:
                param = fn(self.module_full_name, name)
                if hasattr(param, "none_setting"):
                    param = 1
                elif not isinstance(param, int):
                    err = "Invalid `{}` attribute, ".format(name)
                    err += "should be an int. "
                    err += "Got `{}`.".format(param)
                    raise TypeError(err)
                self.i3bar_gaps_module_options[name] = param

        # py3status
        min_length = fn(self.module_full_name, "min_length")
        if not hasattr(min_length, "none_setting"):
            if not isinstance(min_length, int):
                err = "Invalid `min_length` attribute, should be an int. "
                err += "Got `{}`.".format(min_length)
                raise TypeError(err)
            self.py3status_module_options["min_length"] = min_length
            self.random_int = randint(0, 1)

            position = fn(self.module_full_name, "position")
            if not hasattr(position, "none_setting"):
                if position not in POSITIONS:
                    err = "Invalid `position` attribute, should be "
                    err += make_quotes(POSITIONS)
                    err += ". Got `{}`.".format(position)
                    raise ValueError(err)
                self.py3status_module_options["position"] = position

        markup = fn(self.module_full_name, "markup")
        if not hasattr(markup, "none_setting"):
            if markup not in MARKUP_LANGUAGES:
                err = "Invalid `markup` attribute, should be "
                err += make_quotes(MARKUP_LANGUAGES)
                err += ". Got `{}`.".format(markup)
                raise ValueError(err)
            self.py3status_module_options["markup"] = markup

    def process_composite(self, response):
        """
        Process a composite response.
        composites do not have inter item separators as they appear joined.
        We need to respect the universal options too.
        """
        composite = response["composite"]

        # if the composite is of not Composite make it one so we can simplify
        # it.
        if not isinstance(composite, Composite):
            composite = Composite(composite)

        # simplify and get underlying list.
        composite = composite.simplify().get_content()
        response["composite"] = composite

        if not isinstance(composite, list):
            raise Exception('expecting "composite" key in response')
        # if list is empty nothing to do
        if not len(composite):
            return
        if "full_text" in response:
            err = 'conflicting "full_text" and "composite" in response'
            raise Exception(err)

        # set markup
        if "markup" in self.py3status_module_options:
            markup = self.py3status_module_options["markup"]
            line = ""
            for item in composite:
                # validate the response
                if "full_text" not in item:
                    raise KeyError('missing "full_text" key in response')
                color = item.get("color")
                if color:
                    span = u"<span fgcolor='{}'>{}</span>"
                    line += span.format(color, item["full_text"])
                else:
                    line += item["full_text"]
                item["markup"] = markup

        # set universal options on last component
        composite[-1].update(self.i3bar_module_options)
        # update all components
        color = response.get("color")
        urgent = response.get("urgent")
        composite_length = len(response["composite"]) - 1
        for index, item in enumerate(response["composite"]):
            # validate the response
            if "full_text" not in item:
                raise KeyError('missing "full_text" key in response')
            # make sure all components have a name
            if "name" not in item:
                instance_index = item.get("index", index)
                item["instance"] = "{} {}".format(self.module_inst, instance_index)
                item["name"] = self.module_name
            # hide separator for all inner components unless existing
            if index != composite_length:
                if "separator" not in item:
                    item["separator"] = False
                    item["separator_block_width"] = 0
            # If a color was supplied for the composite and a composite
            # part does not supply a color, use the composite color.
            if color and "color" not in item:
                item["color"] = color
            # Remove any none color from our output
            if hasattr(item.get("color"), "none_setting"):
                del item["color"]

            # set background and border colors. set left/right border widths
            # only on first/last composites and no border width for inner
            # composites or we will see border lines between composites.
            for key, value in self.i3bar_gaps_module_options.items():
                if (key == "border_left" and index != 0) or (
                    key == "border_right" and index != composite_length
                ):
                    item[key] = 0
                else:
                    item[key] = value

            # set urgent based on available user-defined settings
            if not self.allow_urgent:
                if "urgent" in item:
                    del item["urgent"]
            elif urgent:
                if self.i3bar_gaps_urgent_options:
                    # set background and border colors. set left/right border widths
                    # only on first/last composites and no border width for inner
                    # composites or we will see border lines between composites.
                    for key, value in self.i3bar_gaps_urgent_options.items():
                        if (key == "border_left" and index != 0) or (
                            key == "border_right" and index != composite_length
                        ):
                            item[key] = 0
                        elif key == "foreground":
                            item["color"] = value
                        else:
                            item[key] = value
                    if "urgent" in item:
                        del item["urgent"]
                else:
                    item["urgent"] = urgent

        # set min_length
        if "min_length" in self.py3status_module_options:
            min_length = self.py3status_module_options["min_length"]

            # get length, skip if length exceeds min_length
            length = sum([len(x["full_text"]) for x in response["composite"]])
            if length >= min_length:
                return

            # sometimes we go under min_length to pad both side evenly,
            # we will add extra space on either side to honor min_length
            padding = int((min_length / 2.0) - (length / 2.0))
            offset = min_length - ((padding * 2) + length)

            # set position
            position = self.py3status_module_options.get("position", "left")
            if position == "center":
                left = right = " " * padding
                if self.random_int:
                    left += " " * offset
                else:
                    right += " " * offset
            elif position == "left":
                left, right = "", " " * (padding * 2 + offset)
            elif position == "right":
                right, left = "", " " * (padding * 2 + offset)

            # padding
            if left:
                response["composite"][0]["full_text"] = (
                    left + response["composite"][0]["full_text"]
                )
            if right:
                response["composite"][-1]["full_text"] += right

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
        if method_name == "on_click":
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
        if not self.module_class:
            # user provided modules take precedence over py3status provided modules
            if self.module_name in user_modules:
                include_path, f_name = user_modules[self.module_name]
                module_path = os.path.join(include_path, f_name)
                self._py3_wrapper.log(
                    'loading module "{}" from {}'.format(module, module_path)
                )
                self.module_class = self.load_from_file(module_path)
            # load from py3status provided modules
            else:
                self._py3_wrapper.log(
                    'loading module "{}" from py3status.modules.{}'.format(
                        module, self.module_name
                    )
                )
                self.module_class = self.load_from_namespace(self.module_name)

        class_inst = self.module_class
        if class_inst:

            try:
                # containers have items attribute set to a list of contained
                # module instance names.  If there are no contained items then
                # ensure that we have a empty list.
                if class_inst.Meta.container:
                    class_inst.items = []
            except AttributeError:
                pass

            # module configuration
            mod_config = self.config["py3_config"].get(module, {})

            # process any deprecated configuration settings
            try:
                deprecated = class_inst.Meta.deprecated
            except AttributeError:
                deprecated = None

            if deprecated:

                def deprecation_log(item):
                    # log the deprecation
                    # currently this is just done to the log file as the user
                    # does not need to take any action.
                    if "msg" in item:
                        msg = item["msg"]
                        param = item.get("param")
                        if param:
                            msg = "`{}` {}".format(param, msg)
                        msg = "DEPRECATION WARNING: {} {}".format(
                            self.module_full_name, msg
                        )
                        self._py3_wrapper.log(msg)

                if "rename" in deprecated:
                    # renamed parameters
                    for item in deprecated["rename"]:
                        param = item["param"]
                        new_name = item["new"]
                        if param in mod_config:
                            if new_name not in mod_config:
                                mod_config[new_name] = mod_config[param]
                                # remove from config
                                del mod_config[param]
                            deprecation_log(item)
                if "format_fix_unnamed_param" in deprecated:
                    # format update where {} was previously allowed
                    for item in deprecated["format_fix_unnamed_param"]:
                        param = item["param"]
                        placeholder = item["placeholder"]
                        if "{}" in mod_config.get(param, ""):
                            mod_config[param] = mod_config[param].replace(
                                "{}", "{%s}" % placeholder
                            )
                            deprecation_log(item)
                if "rename_placeholder" in deprecated:
                    # rename placeholders
                    placeholders = {}
                    for item in deprecated["rename_placeholder"]:
                        placeholders[item["placeholder"]] = item["new"]
                        format_strings = item["format_strings"]
                        for format_param in format_strings:
                            format_string = mod_config.get(format_param)
                            if not format_string:
                                continue
                            format = Formatter().update_placeholders(
                                format_string, placeholders
                            )
                            mod_config[format_param] = format

                if "update_placeholder_format" in deprecated:
                    # update formats for placeholders if a format is not set
                    for item in deprecated["update_placeholder_format"]:
                        placeholder_formats = item.get("placeholder_formats", {})
                        if "function" in item:
                            placeholder_formats.update(item["function"](mod_config))
                        format_strings = item["format_strings"]
                        for format_param in format_strings:
                            format_string = mod_config.get(format_param)
                            if not format_string:
                                continue
                            format = Formatter().update_placeholder_formats(
                                format_string, placeholder_formats
                            )
                            mod_config[format_param] = format
                if "substitute_by_value" in deprecated:
                    # one parameter sets the value of another
                    for item in deprecated["substitute_by_value"]:
                        param = item["param"]
                        value = item["value"]
                        substitute = item["substitute"]
                        substitute_param = substitute["param"]
                        substitute_value = substitute["value"]
                        if (
                            mod_config.get(param) == value
                            and substitute_param not in mod_config
                        ):
                            mod_config[substitute_param] = substitute_value
                            deprecation_log(item)
                if "function" in deprecated:
                    # parameter set by function
                    for item in deprecated["function"]:
                        updates = item["function"](mod_config)
                        for name, value in updates.items():
                            if name not in mod_config:
                                mod_config[name] = value
                if "remove" in deprecated:
                    # obsolete parameters forcibly removed
                    for item in deprecated["remove"]:
                        param = item["param"]
                        if param in mod_config:
                            del mod_config[param]
                            deprecation_log(item)

            # apply module configuration
            for config, value in mod_config.items():
                # names starting with '.' are private
                if not config.startswith("."):
                    setattr(self.module_class, config, value)

            # process any update_config settings
            try:
                update_config = class_inst.Meta.update_config
            except AttributeError:
                update_config = None

            if update_config:
                if "update_placeholder_format" in update_config:
                    # update formats for placeholders if a format is not set
                    for item in update_config["update_placeholder_format"]:
                        placeholder_formats = item.get("placeholder_formats", {})
                        format_strings = item["format_strings"]
                        for format_param in format_strings:
                            format_string = getattr(class_inst, format_param, None)
                            if not format_string:
                                continue
                            format = Formatter().update_placeholder_formats(
                                format_string, placeholder_formats
                            )
                            setattr(class_inst, format_param, format)

            # Add the py3 module helper if modules self.py3 is not defined
            if not hasattr(self.module_class, "py3"):
                setattr(self.module_class, "py3", Py3(self))

            # Subscribe to udev events if on_udev_* dynamic variables are
            # configured on the module
            for param in dir(self.module_class):
                if param.startswith("on_udev_"):
                    trigger_action = getattr(self.module_class, param)
                    self.add_udev_trigger(trigger_action, param[8:])

            # allow_urgent
            # get the value form the config or use the module default if
            # supplied.
            fn = self._py3_wrapper.get_config_attribute
            param = fn(self.module_full_name, "allow_urgent")
            if hasattr(param, "none_setting"):
                param = True
            self.allow_urgent = param

            # urgent background
            urgent_background = fn(self.module_full_name, "urgent_background")
            if not hasattr(urgent_background, "none_setting"):
                color = self.module_class.py3._get_color(urgent_background)
                if not color:
                    err = "Invalid `urgent_background` attribute, should be "
                    err += "a color. Got `{}`.".format(urgent_background)
                    raise ValueError(err)
                self.i3bar_gaps_urgent_options["background"] = color

            # urgent foreground
            urgent_foreground = fn(self.module_full_name, "urgent_foreground")
            if not hasattr(urgent_foreground, "none_setting"):
                color = self.module_class.py3._get_color(urgent_foreground)
                if not color:
                    err = "Invalid `urgent_foreground` attribute, should be "
                    err += "a color. Got `{}`.".format(urgent_foreground)
                    raise ValueError(err)
                self.i3bar_gaps_urgent_options["foreground"] = color

            # urgent urgent_borders
            urgent_border = fn(self.module_full_name, "urgent_border")
            if not hasattr(urgent_border, "none_setting"):
                color = self.module_class.py3._get_color(urgent_border)
                if not color:
                    err = "Invalid `urgent_border` attribute, should be a color. "
                    err += "Got `{}`.".format(urgent_border)
                    raise ValueError(err)
                self.i3bar_gaps_urgent_options["border"] = color

                urgent_borders = ["top", "right", "bottom", "left"]
                for name in ["urgent_border_" + x for x in urgent_borders]:
                    param = fn(self.module_full_name, name)
                    if hasattr(param, "none_setting"):
                        param = 1
                    elif not isinstance(param, int):
                        err = "Invalid `{}` attribute, ".format(name)
                        err += "should be an int. "
                        err += "Got `{}`.".format(param)
                        raise TypeError(err)
                    self.i3bar_gaps_urgent_options[name[7:]] = param

            # get the available methods for execution
            for method in sorted(dir(class_inst)):
                if method.startswith("_"):
                    continue
                else:
                    m_type = type(getattr(class_inst, method))
                    if "method" in str(m_type):
                        params_type = self._params_type(method, class_inst)
                        if method == "on_click":
                            self.click_events = params_type
                        elif method == "kill":
                            self.has_kill = params_type
                        elif method == "post_config_hook":
                            self.has_post_config_hook = True
                        else:
                            # the method_obj stores infos about each method
                            # of this module.
                            method_obj = {
                                "cached_until": time(),
                                "call_type": params_type,
                                "instance": None,
                                "last_output": {"name": method, "full_text": ""},
                                "method": method,
                                "name": None,
                            }
                            self.methods[method] = method_obj

        # done, log some debug info
        if self.config["debug"]:
            self._py3_wrapper.log(
                'module "{}" click_events={} has_kill={} methods={}'.format(
                    module, self.click_events, self.has_kill, self.methods.keys()
                )
            )

    def click_event(self, event):
        """
        Execute the 'on_click' method of this module with the given event.
        """
        # we can prevent request that a refresh after the event has happened
        # by setting this to True.  Modules should do this via
        # py3.prevent_refresh()
        self.prevent_refresh = False
        try:
            if self.error_messages:
                # we have error messages
                button = event["button"]
                if button == 1:
                    # cycle through to next message
                    self.error_index = (self.error_index + 1) % len(self.error_messages)
                    error = self.error_messages[self.error_index]
                    self.error_output(error)
                if button == 3:
                    self.hide_errors()
                if button != 2 or (self.terminated or self.disabled):
                    self.prevent_refresh = True

            elif self.click_events:
                click_method = getattr(self.module_class, "on_click")
                if self.click_events == self.PARAMS_NEW:
                    # new style modules
                    click_method(event)
                else:
                    # legacy modules had extra parameters passed
                    click_method(
                        self.i3status_thread.json_list,
                        self.config["py3_config"]["general"],
                        event,
                    )
                self.set_updated()
            else:
                # nothing has happened so no need for refresh
                self.prevent_refresh = True
        except Exception:
            msg = "on_click event in `{}` failed".format(self.module_full_name)
            self._py3_wrapper.report_exception(msg)

    @profile
    def run(self):
        """
        On a timely fashion, execute every method found for this module.
        We will respect and set a cache timeout for each method if the user
        didn't already do so.
        We will execute the 'kill' method of the module when we terminate.
        """
        if self._py3_wrapper.running:
            cache_time = None
            # execute each method of this module
            for meth, obj in self.methods.items():
                my_method = self.methods[meth]

                # always check py3status is running
                if not self._py3_wrapper.running:
                    break

                # respect the cache set for this method
                if time() < obj["cached_until"]:
                    if not cache_time or obj["cached_until"] < cache_time:
                        cache_time = obj["cached_until"]
                    continue

                try:
                    # execute method and get its output
                    method = getattr(self.module_class, meth)
                    if my_method["call_type"] == self.PARAMS_NEW:
                        # new style modules
                        response = method()
                    else:
                        # legacy modules had parameters passed
                        response = method(
                            self.i3status_thread.json_list,
                            self.config["py3_config"]["general"],
                        )

                    if isinstance(response, dict):
                        # this is a shiny new module giving a dict response
                        result = response
                    elif isinstance(response, tuple):
                        # this is an old school module reporting its position
                        position, result = response
                        if not isinstance(result, dict):
                            raise TypeError("response should be a dict")
                    else:
                        raise TypeError("response should be a dict")

                    if isinstance(response.get("full_text"), (list, Composite)):
                        response["composite"] = response["full_text"]
                        del response["full_text"]
                    if "composite" in response:
                        self.process_composite(response)
                    else:
                        # validate the response
                        if "full_text" not in result:
                            err = 'missing "full_text" key in response'
                            raise KeyError(err)
                        # Remove any none color from our output
                        if hasattr(result.get("color"), "none_setting"):
                            del result["color"]
                        # remove urgent if not allowed
                        if not self.allow_urgent and "urgent" in result:
                            del result["urgent"]
                        # set universal module options in result
                        result.update(self.i3bar_module_options)

                    result["instance"] = self.module_inst
                    result["name"] = self.module_name

                    # initialize method object
                    if my_method["name"] is None:
                        my_method["name"] = result["name"]
                        if "instance" in result:
                            my_method["instance"] = result["instance"]
                        else:
                            my_method["instance"] = result["name"]

                    # update method object cache
                    if "cached_until" in result:
                        cached_until = result["cached_until"]
                        # remove this so we can check later for output changes
                        del result["cached_until"]
                    else:
                        # get module default cached_until
                        cached_until = self.module_class.py3.time_in()
                    my_method["cached_until"] = cached_until
                    if not cache_time or cached_until < cache_time:
                        cache_time = cached_until

                    # update method object output
                    if "composite" in response:
                        my_method["last_output"] = result["composite"]
                    else:
                        my_method["last_output"] = result

                    # debug info
                    if self.config["debug"]:
                        self._py3_wrapper.log(
                            "method {} returned {} ".format(meth, result)
                        )
                    # module working correctly so ensure module works as
                    # expected
                    self.allow_config_clicks = True
                    self.error_messages = None
                    self.error_hide = False

                    # mark module as updated
                    self.set_updated()

                except ModuleErrorException as e:
                    # module has indicated that it has an error
                    self.runtime_error(e.msg, meth)
                    if e.timeout:
                        if e.timeout is PY3_CACHE_FOREVER:
                            cache_time = PY3_CACHE_FOREVER
                        else:
                            cache_time = time() + e.timeout
                    else:
                        cache_time = time() + getattr(
                            self.module_class,
                            "cache_timeout",
                            self.config["cache_timeout"],
                        )

                except Exception as e:
                    msg = "Instance `{}`, user method `{}` failed"
                    msg = msg.format(self.module_full_name, meth)
                    if not self.testing:
                        self._py3_wrapper.report_exception(msg, notify_user=False)
                    # added error
                    self.runtime_error(str(e) or e.__class__.__name__, meth)
                    cache_time = time() + getattr(
                        self.module_class, "cache_timeout", self.config["cache_timeout"]
                    )

            if cache_time is None:
                cache_time = time() + self.config["cache_timeout"]
            self.cache_time = cache_time
            # new style modules can signal they want to cache forever
            if cache_time == PY3_CACHE_FOREVER:
                return
            # don't be hasty mate
            # set timeout to do update next time one is needed
            if not cache_time:
                cache_time = time() + self.config["minimum_interval"]

            self._py3_wrapper.timeout_queue_add(self, cache_time)

    def kill(self):
        # check and execute the 'kill' method if present
        if self.has_kill:
            try:
                kill_method = getattr(self.module_class, "kill")
                if self.has_kill == self.PARAMS_NEW:
                    kill_method()
                else:
                    # legacy call parameters
                    kill_method(
                        self.i3status_thread.json_list,
                        self.config["py3_config"]["general"],
                    )
            except Exception:
                # this would be stupid to die on exit
                pass

    def add_udev_trigger(self, trigger_action, subsystem):
        """
        Subscribe to the requested udev subsystem and apply the given action.
        """
        if self._py3_wrapper.udev_monitor.subscribe(self, trigger_action, subsystem):
            if trigger_action == "refresh_and_freeze":
                # FIXME: we may want to disable refresh instead of using cache_timeout
                self.module_class.cache_timeout = PY3_CACHE_FOREVER
