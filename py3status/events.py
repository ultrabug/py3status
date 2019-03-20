import select
import sys

from threading import Thread
from subprocess import Popen, PIPE
from json import loads

from py3status.profiling import profile

try:
    # Python 3
    from shlex import quote as shell_quote
except ImportError:
    # Python 2
    from pipes import quote as shell_quote


class IOPoller:
    """
    This class implements a predictive and timing-out I/O reader
    using select and the poll() mechanism for greater compatibility.
    """

    def __init__(self, io, eventmask=select.POLLIN):
        """
        Our default is to read (POLLIN) the specified 'io' file descriptor.
        """
        self.io = io
        self.poller = select.poll()
        self.poller.register(io, eventmask)

    def readline(self, timeout=500):
        """
        Try to read our I/O for 'timeout' milliseconds, return None otherwise.
        This makes calling and reading I/O non blocking !
        """
        poll_result = self.poller.poll(timeout)
        if poll_result:
            line = self.io.readline().strip()
            if self.io == sys.stdin and line == "[":
                # skip first event line wrt issue #19
                line = self.io.readline().strip()
            try:
                # python3 compatibility code
                line = line.decode()
            except (AttributeError, UnicodeDecodeError):
                pass
            return line
        else:
            return None


class EventTask:
    """
    A simple task that can be run by the scheduler.
    """

    def __init__(self, module_name, event, default_event, events_thread):
        self.events_thread = events_thread
        self.module_full_name = module_name
        self.default_event = default_event
        self.event = event

    def run(self):
        self.events_thread.process_event(
            self.module_full_name, self.event, self.default_event
        )


class EventClickTask:
    """
    A task to run an external on_click event
    """

    def __init__(self, module_name, event, events_thread, command):
        self.events_thread = events_thread
        self.module_name = module_name
        self.command = command
        self.event = event

    def run(self):
        self.events_thread.on_click_dispatcher(
            self.module_name, self.event, self.command
        )


class Events(Thread):
    """
    This class is responsible for dispatching event JSONs sent by the i3bar.
    """

    def __init__(self, py3_wrapper):
        """
        We need to poll stdin to receive i3bar messages.
        """
        Thread.__init__(self)
        self.config = py3_wrapper.config
        self.error = None
        self.py3_config = py3_wrapper.config["py3_config"]
        self.modules = py3_wrapper.modules
        self.on_click = self.py3_config["on_click"]
        self.output_modules = py3_wrapper.output_modules
        self.poller_inp = IOPoller(sys.stdin)
        self.py3_wrapper = py3_wrapper

    def get_module_text(self, module_name, event):
        """
        Get the full text for the module as well as the partial text if the
        module is a composite.  Partial text is the text for just the single
        section of a composite.
        """
        index = event.get("index")
        module_info = self.py3_wrapper.output_modules.get(module_name)
        output = module_info["module"].get_latest()
        full_text = u"".join([out["full_text"] for out in output])

        partial = None
        if index is not None:
            if isinstance(index, int):
                partial = output[index]
            else:
                for item in output:
                    if item.get("index") == index:
                        partial = item
                        break
        if partial:
            partial_text = partial["full_text"]
        else:
            partial_text = full_text
        return full_text, partial_text

    def on_click_dispatcher(self, module_name, event, command):
        """
        Dispatch on_click config parameters to either:
            - Our own methods for special py3status commands (listed below)
            - The i3-msg program which is part of i3wm
        """
        if command is None:
            return
        elif command == "refresh_all":
            self.py3_wrapper.refresh_modules()
        elif command == "refresh":
            self.py3_wrapper.refresh_modules(module_name)
        else:
            # In commands we are able to use substitutions for the text output
            # of a module
            if "$OUTPUT" in command or "$OUTPUT_PART" in command:
                full_text, partial_text = self.get_module_text(module_name, event)
                command = command.replace("$OUTPUT_PART", shell_quote(partial_text))
                command = command.replace("$OUTPUT", shell_quote(full_text))

            # this is a i3 message
            self.wm_msg(module_name, command)
            # to make the bar more responsive to users we ask for a refresh
            # of the module or of i3status if the module is an i3status one
            self.py3_wrapper.refresh_modules(module_name)

    def wm_msg(self, module_name, command):
        """
        Execute the message with i3-msg or swaymsg and log its output.
        """
        wm_msg = self.config["wm"]["msg"]
        pipe = Popen([wm_msg, command], stdout=PIPE)
        self.py3_wrapper.log(
            '{} module="{}" command="{}" stdout={}'.format(
                wm_msg, module_name, command, pipe.stdout.read()
            )
        )

    def process_event(self, module_name, event, default_event=False):
        """
        Process the event for the named module.
        Events may have been declared in i3status.conf, modules may have
        on_click() functions. There is a default middle click event etc.
        """

        # get the module that the event is for
        module_info = self.output_modules.get(module_name)

        # if module is a py3status one call it.
        if module_info["type"] == "py3status":
            module = module_info["module"]
            module.click_event(event)
            if self.config["debug"]:
                self.py3_wrapper.log("dispatching event {}".format(event))

            # to make the bar more responsive to users we refresh the module
            # unless the on_click event called py3.prevent_refresh()
            if not module.prevent_refresh:
                self.py3_wrapper.refresh_modules(module_name)
                default_event = False

        if default_event:
            # default button 2 action is to clear this method's cache
            if self.config["debug"]:
                self.py3_wrapper.log("dispatching default event {}".format(event))
            self.py3_wrapper.refresh_modules(module_name)

        # find container that holds the module and call its onclick
        module_groups = self.py3_config[".module_groups"]
        containers = module_groups.get(module_name, [])
        for container in containers:
            self.process_event(container, event)

    def dispatch_event(self, event):
        """
        Takes an event dict.  Logs the event if needed and cleans up the dict
        such as setting the index needed for composits.
        """
        if self.config["debug"]:
            self.py3_wrapper.log("received event {}".format(event))

        # usage variables
        event["index"] = event.get("index", "")
        instance = event.get("instance", "")
        name = event.get("name", "")

        # composites have an index which is passed to i3bar with
        # the instance.  We need to separate this out here and
        # clean up the event.  If index
        # is an integer type then cast it as such.
        if " " in instance:
            instance, index = instance.split(" ", 1)
            try:
                index = int(index)
            except ValueError:
                pass
            event["index"] = index
            event["instance"] = instance

        if self.config["debug"]:
            self.py3_wrapper.log(
                'trying to dispatch event to module "{}"'.format(
                    "{} {}".format(name, instance).strip()
                )
            )

        # guess the module config name
        module_name = "{} {}".format(name, instance).strip()

        default_event = False
        module_info = self.output_modules.get(module_name)
        if not module_info:
            return
        module = module_info["module"]
        # execute any configured i3-msg command
        # we do not do this for containers
        # modules that have failed do not execute their config on_click
        if module.allow_config_clicks:
            button = event.get("button", 0)
            on_click = self.on_click.get(module_name, {}).get(str(button))
            if on_click:
                task = EventClickTask(module_name, event, self, on_click)
                self.py3_wrapper.timeout_queue_add(task)
            # otherwise setup default action on button 2 press
            elif button == 2:
                default_event = True

        # do the work
        task = EventTask(module_name, event, default_event, self)
        self.py3_wrapper.timeout_queue_add(task)

    @profile
    def run(self):
        """
        Wait for an i3bar JSON event, then find the right module to dispatch
        the message to based on the 'name' and 'instance' of the event.

        In case the module does NOT support click_events, the default
        implementation is to clear the module's cache
        when the MIDDLE button (2) is pressed on it.

        Example event:
        {'y': 13, 'x': 1737, 'button': 1, 'name': 'empty', 'instance': 'first'}
        """
        try:
            while self.py3_wrapper.running:
                event_str = self.poller_inp.readline()
                if not event_str:
                    continue
                try:
                    # remove leading comma if present
                    if event_str[0] == ",":
                        event_str = event_str[1:]
                    event = loads(event_str)
                    self.dispatch_event(event)
                except Exception:
                    self.py3_wrapper.report_exception("Event failed")
        except:  # noqa e722
            err = "Events thread died, click events are disabled."
            self.py3_wrapper.report_exception(err, notify_user=False)
            self.py3_wrapper.notify_user(err, level="warning")
