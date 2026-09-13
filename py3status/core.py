import importlib.metadata
import logging
import logging.config
import logging.handlers
import sys
import time
from collections import deque
from pathlib import Path
from signal import SIGCONT, SIGTERM, SIGTSTP, SIGUSR1, Signals, signal
from subprocess import Popen
from threading import Event, Thread

from py3status.command import CommandServer
from py3status.common import Common
from py3status.constants import LOGGING_CONFIG, LOGGING_LOG_FILE_CONFIG
from py3status.events import Events
from py3status.helpers import get_module_name
from py3status.i3status.constants import I3S_PROXY_TYPE
from py3status.i3status.helpers import is_i3status_container_name, is_i3status_proxy_name
from py3status.i3status.proxy import Py3status as I3statusProxy
from py3status.log import module_logger_name, resolve_log_level
from py3status.module import Module
from py3status.output import OutputFormat
from py3status.parse_config import process_config
from py3status.profiling import profile
from py3status.udev_monitor import UdevMonitor

DBUS_LEVELS = {"error": "critical", "warning": "normal", "info": "low"}

CONFIG_SPECIAL_SECTIONS = [
    ".module_groups",
    "general",
    "on_click",
    "order",
    "py3_modules",
    "py3status",
]

ENTRY_POINT_NAME = "py3status"
ENTRY_POINT_KEY = "entry_point"
logger = logging.getLogger(__name__)


class Runner(Thread):
    """
    A Simple helper to run a module in a Thread so it is non-locking.
    """

    def __init__(self, module, py3_wrapper, module_name):
        Thread.__init__(self)
        self.daemon = True
        self.module = module
        self.module_name = module_name
        self.py3_wrapper = py3_wrapper
        self.start()

    def run(self):
        try:
            self.module.run()
        except:  # noqa e722
            self.py3_wrapper.report_exception("Runner")
        # the module is no longer running so notify the timeout logic
        if self.module_name:
            self.py3_wrapper.timeout_finished.append(self.module_name)


class Task:
    """
    A simple task that can be run by the scheduler.
    """

    def run(self):
        # F901 'raise NotImplemented' should be 'raise NotImplementedError'
        raise NotImplemented()  # noqa f901


class ModuleRunner(Task):
    """
    Starts up a Module
    """

    def __init__(self, module):
        self.module = module

    def run(self):
        self.module.start_module()


class Py3statusWrapper:
    """
    This is the py3status wrapper.
    """

    def __init__(self, options):
        """
        Useful variables we'll need.
        """
        self.config = vars(options)
        self.i3bar_running = True
        self.inhibit_signal_ts = time.monotonic()
        self.last_refresh_ts = time.monotonic()
        self.lock = Event()
        self.modules = {}
        self.next_allowed_signal = SIGTSTP
        self.notified_messages = set()
        self.options = options
        self.output_modules = {}
        self.py3_modules = []
        self.loaded_entry_points = None
        self.running = True
        self.stop_signal = SIGTSTP
        self.update_queue = deque()
        self.update_request = Event()

        # shared code
        self.common = Common(self)
        self.get_config_attribute = self.common.get_config_attribute
        self.report_exception = self.common.report_exception

        # these are used to schedule module updates
        self.timeout_add_queue = deque()
        self.timeout_due = None
        self.timeout_finished = deque()
        self.timeout_keys = []
        self.timeout_missed = {}
        self.timeout_queue = {}
        self.timeout_queue_lookup = {}
        self.timeout_queue_lookup_previous = {}
        self.timeout_running = set()
        self.timeout_update_due = deque()

    def timeout_queue_add(self, item, cache_time=0):
        """
        Add a item to be run at a future time.
        This must be a Module or a Task
        """
        # add the info to the add queue.  We do this so that actually adding
        # the module is done in the core thread.
        self.timeout_add_queue.append((item, cache_time))
        # if the timeout_add_queue is not due to be processed until after this
        # update request is due then trigger an update now.
        if self.timeout_due is None or cache_time < self.timeout_due:
            self.update_request.set()

    def clear_timeout_due(self, module):
        old = self.timeout_queue_lookup_previous.get(module, None)
        if old:
            if old == self.timeout_due:
                self._set_new_timeout_due()
            elif old in self.timeout_keys:
                self.timeout_keys.remove(old)
                self._set_new_timeout_due()

    def _set_new_timeout_due(self):
        # sort keys so earliest is first
        self.timeout_keys.sort()

        # when is next timeout due?
        try:
            self.timeout_due = self.timeout_keys[0]
        except IndexError:
            self.timeout_due = None

    def timeout_process_add_queue(self, module, cache_time):
        """
        Add a module to the timeout_queue if it is scheduled in the future or
        if it is due for an update immediately just trigger that.

        the timeout_queue is a dict with the scheduled time as the key and the
        value is a list of module instance names due to be updated at that
        point. An ordered list of keys is kept to allow easy checking of when
        updates are due.  A list is also kept of which modules are in the
        update_queue to save having to search for modules in it unless needed.
        """
        # If already set to update do nothing
        if module in self.timeout_update_due:
            return

        # remove if already in the queue
        key = self.timeout_queue_lookup.get(module, None)
        if key:
            queue_item = self.timeout_queue[key]
            queue_item.remove(module)
            if not queue_item:
                del self.timeout_queue[key]
                self.timeout_keys.remove(key)

        if cache_time == 0:
            # if cache_time is 0 we can just trigger the module update
            self.timeout_update_due.append(module)
            if module in self.timeout_queue_lookup.keys():
                del self.timeout_queue_lookup[module]
        else:
            # add the module to the timeout queue
            if cache_time not in self.timeout_keys:
                self.timeout_queue[cache_time] = {module}
                self.timeout_keys.append(cache_time)

                self._set_new_timeout_due()
            else:
                self.timeout_queue[cache_time].add(module)
            # note that the module is in the timeout_queue
            self.timeout_queue_lookup[module] = cache_time
            self.timeout_queue_lookup_previous[module] = cache_time

    def timeout_queue_process(self):
        """
        Check the timeout_queue and set any due modules to update.
        """
        # process any items that need adding to the queue
        while self.timeout_add_queue:
            self.timeout_process_add_queue(*self.timeout_add_queue.popleft())
        now = time.monotonic()
        due_timeouts = []
        # find any due timeouts
        for timeout in self.timeout_keys:
            if timeout > now:
                break
            due_timeouts.append(timeout)

        if due_timeouts:
            # process them
            for timeout in due_timeouts:
                modules = self.timeout_queue[timeout]
                # remove from the queue
                del self.timeout_queue[timeout]
                self.timeout_keys.remove(timeout)

                for module in modules:
                    # module no longer in queue
                    del self.timeout_queue_lookup[module]
                    # tell module to update
                    self.timeout_update_due.append(module)

            # when is next timeout due?
            try:
                self.timeout_due = self.timeout_keys[0]
            except IndexError:
                self.timeout_due = None

        # process any finished modules.
        # Now that the module has finished running it may have been marked to
        # be triggered again. This is most likely to happen when events are
        # being processed and the events are arriving much faster than the
        # module can handle them.  It is important as a module may handle
        # events but not trigger the module update.  If during the event the
        # module is due to update the update is not actioned but it needs to be
        # once the events have finished or else the module will no longer
        # continue to update.
        while self.timeout_finished:
            module_name = self.timeout_finished.popleft()
            self.timeout_running.discard(module_name)
            if module_name in self.timeout_missed:
                module = self.timeout_missed.pop(module_name)
                self.timeout_update_due.append(module)

        # run any modules that are due
        while self.timeout_update_due:
            module = self.timeout_update_due.popleft()
            module_name = getattr(module, "module_full_name", None)
            # if the module is running then we do not want to trigger it but
            # instead wait till it has finished running and then trigger
            if module_name and module_name in self.timeout_running:
                self.timeout_missed[module_name] = module
            else:
                self.timeout_running.add(module_name)
                Runner(module, self, module_name)

        # we return how long till we next need to process the timeout_queue
        # this value should not be negative to avoid cpu overwhelming loops
        if self.timeout_due is not None:
            return max(0, self.timeout_due - time.monotonic())

    def _get_default_modules(self):
        modules_path = Path(__file__).resolve().parent / "modules"
        return sorted(
            p.stem for p in modules_path.iterdir() if p.suffix == ".py" and p.stem != "__init__"
        )

    def get_discoverable_modules(self):
        """Mapping from module name to relevant objects.

        There are two ways of discovery and storage:
        `include_paths` (no installation): include_path, f_name
        `entry_point` (from installed package): "entry_point", <Py3Status class>

        Modules of the same name from entry-point packages shadow all other modules.
        """
        discoverable_modules = self._get_path_included_modules()
        discoverable_modules.update(self._get_entry_point_based_modules())
        # i3status_proxy has no file in py3status/modules/ - load it like an
        # entry-point module, via a pre-built instance, not by import path.
        discoverable_modules[I3S_PROXY_TYPE] = (ENTRY_POINT_KEY, I3statusProxy)
        return discoverable_modules

    def _get_path_included_modules(self):
        """
        Search configured include directories for user provided modules.

        path_included_modules: {
            'weather_yahoo': ('~/i3/py3status/', 'weather_yahoo.py')
        }
        """
        path_included_modules = {}
        for include_path in self.config["include_paths"]:
            for f_name in include_path.iterdir():
                if f_name.suffix != ".py":
                    continue
                module_name = f_name.stem
                # do not overwrite modules if already found
                if module_name in path_included_modules:
                    continue
                path_included_modules[module_name] = (include_path, f_name)
        return dict(sorted(path_included_modules.items()))

    def _get_loaded_entry_points(self):
        if self.loaded_entry_points is not None:
            return self.loaded_entry_points

        loaded_entry_points = []
        eps = importlib.metadata.entry_points(group=ENTRY_POINT_NAME)

        for entry_point in eps:
            try:
                module = entry_point.load()
            except Exception as err:
                logger.error(
                    "entry-point module '%s' (%s) %s",
                    entry_point.name,
                    entry_point.value,
                    err,
                )
                continue
            klass = getattr(module, Module.EXPECTED_CLASS, None)
            if klass:
                loaded_entry_points.append(
                    (entry_point.name.split(".")[-1], entry_point.value, klass)
                )
        self.loaded_entry_points = loaded_entry_points
        return self.loaded_entry_points

    def _get_entry_point_based_modules(self):
        classes_from_entry_points = {}
        for module_name, _value, klass in self._get_loaded_entry_points():
            classes_from_entry_points[module_name] = (ENTRY_POINT_KEY, klass)
        return classes_from_entry_points

    def _get_entry_point_debug_modules(self):
        return sorted(
            f"{module_name} ({value})"
            for module_name, value, _klass in self._get_loaded_entry_points()
        )

    def get_configured_discoverable_modules(self):
        """
        Get a dict of all configured discoverable py3status modules
        in the user's i3status.conf.

        As we already have a convenient way of loading the module, we'll
        populate the map with the Py3Status class right away
        """
        discoverable_modules = {}
        if not self.py3_modules:
            return discoverable_modules
        for module_name, module_info in self.get_discoverable_modules().items():
            for module in self.py3_modules:
                if module_name == get_module_name(module):
                    source, item = module_info
                    discoverable_modules[module_name] = (source, item)
        return discoverable_modules

    def load_modules(self, modules_list, discoverable_modules):
        """
        Load the given modules from the list (contains instance name) with
        respect to the discoverable modules dict.

        modules_list: ['weather_yahoo paris', 'pewpew', 'net_rate']
        discoverable_modules: {
            'weather_yahoo': ('/etc/py3status.d/', 'weather_yahoo.py'),
            'pewpew': ('entry_point', <Py3Status class>),  # entry-point module
        }
        """
        for module in modules_list:
            # ignore already provided modules (prevents double inclusion)
            if module in self.modules:
                continue
            try:
                instance = None
                payload = discoverable_modules.get(get_module_name(module))
                if payload:
                    kind, Klass = payload
                    if kind == ENTRY_POINT_KEY:
                        instance = Klass()
                my_m = Module(module, discoverable_modules, self, instance=instance)
                # only handle modules with available methods
                if my_m.methods:
                    self.modules[module] = my_m
                else:
                    logger.debug("ignoring module '%s' (no methods found)", module)
            except Exception:
                err = sys.exc_info()[1]
                msg = f'loading module "{module}" failed ({err})'
                self.report_exception(msg, level="warning")

    def _setup_logging(self):
        """
        Set up logging_config, log_file, debug, et cetera.
        """

        def _deep_merge(base, override):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    _deep_merge(base[key], value)
                else:
                    base[key] = value

        init_logging_config = dict(LOGGING_CONFIG)
        user_logging_config = (
            self.config.get("py3_config", {}).get("py3status", {}).get("logging", {})
        )
        _deep_merge(init_logging_config, user_logging_config)

        if self.config.get("debug"):
            init_logging_config["root"]["level"] = "DEBUG"

        if self.config.get("log_file"):
            handler_name, handler_cfg = next(iter(LOGGING_LOG_FILE_CONFIG.items()))
            handler_cfg = dict(handler_cfg)
            handler_cfg["filename"] = self.config["log_file"]
            init_logging_config["handlers"][handler_name] = handler_cfg
            user_root_handlers = user_logging_config.get("root", {}).get("handlers")
            if user_root_handlers is None:
                init_logging_config["root"]["handlers"] = [handler_name]
            elif handler_name not in init_logging_config["root"]["handlers"]:
                init_logging_config["root"]["handlers"].append(handler_name)

        logging.config.dictConfig(init_logging_config)

        # Set the syslog identifier so logs can be filtered with journalctl -t py3status
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.handlers.SysLogHandler):
                handler.ident = "py3status: "

    def _log_gitversion(self):
        # A git repo is detected looking for the .git directory

        git_path = Path(__file__).resolve().parent.parent / ".git"
        if not git_path.exists():
            return

        logger.info("running within git repo")

        try:
            import git
        except ImportError:
            repo = None
        else:
            try:
                repo = git.Repo(git_path.parent)
            except Exception:
                repo = None

        if not repo:
            try:
                with (git_path / "HEAD").open() as f:
                    out = f.readline()
            except OSError:
                logger.warning(
                    "unable to read git HEAD, use python git package for more repo information"
                )
                return
            branch = "/".join(out.strip().split("/")[2:])
            logger.info("git branch: %s", branch)
            # last commit
            log_path = git_path / "logs" / "refs" / "heads" / branch
            with log_path.open() as f:
                out = f.readlines()[-1]
            sha = out.split(" ")[1][:7]
            msg = ":".join(out.strip().split("\t")[-1].split(":")[1:])
            logger.info("git commit: %s%s", sha, msg)
        else:
            commit = repo.head.commit
            logger.info("git branch: %s", repo.active_branch.name)
            logger.info("git commit: %s %s", commit.hexsha[:7], commit.summary)
            logger.info("git clean: %s", not repo.is_dirty())

    def setup(self):
        """
        Setup py3status and spawn events/modules threads. i3status runs
        as a regular module now, started the same way as any other.
        """
        # set up early, so config-parse notify_user() calls get logged too
        self._setup_logging()

        # process py3status config
        config_path = self.config["config"]
        py3_config = process_config(config_path, self)
        self.config["py3_config"] = py3_config
        # re-apply: picks up any py3status logging override
        self._setup_logging()

        # log py3status and python versions
        logger.info("=" * 8)
        msg = "starting py3status version {version} python {python_version}"
        logger.info(msg.format(**self.config))

        # if running from git then log the branch and last commit
        self._log_gitversion()

        # log config file and window manager
        logger.info("config file: %s", self.config["config"])
        logger.info("window manager: %s", self.config["wm_name"])
        logger.debug("py3status started with config %s", self.config)

        # autodetect output_format
        output_format = self.config["py3_config"]["general"]["output_format"]
        if output_format is None:
            if sys.stdout.isatty():
                print("py3status: trying to auto-detect output_format setting")
                print('py3status: auto-detected "term"')
                output_format = "term"

        self.config["py3_config"]["general"]["output_format"] = output_format or "i3bar"

        # read resources
        if "resources" in str(self.config["py3_config"].values()):
            from subprocess import check_output

            resources = check_output(["xrdb", "-query"]).decode().splitlines()
            self.config["resources"] = {
                k: v.strip() for k, v in (x.split(":", 1) for x in resources)
            }

        # setup input events thread
        self.events_thread = Events(self)
        self.events_thread.daemon = True
        self.events_thread.start()
        logger.debug("events thread started")

        # initialise the command server
        self.commands_thread = CommandServer(self)
        self.commands_thread.daemon = True
        self.commands_thread.start()
        logger.debug("commands thread started")

        # initialize the udev monitor (lazy)
        self.udev_monitor = UdevMonitor(self)

        # suppress modules' output wrt issue #20
        if not self.config["debug"]:
            sys.stdout = Path("/dev/null").open("w")
            sys.stderr = Path("/dev/null").open("w")

        # make sure we honor custom i3bar protocol stop/resume signals
        # while providing users a way to opt out from that feature
        # using the 0 value as specified by the i3bar protocol
        custom_stop_signal = self.config["py3_config"].get("py3status", {}).get("stop_signal")
        if custom_stop_signal is not None:
            try:
                # 0 is a special value for i3bar protocol, use it as-is
                if custom_stop_signal == 0:
                    self.stop_signal = custom_stop_signal
                else:
                    self.stop_signal = Signals(custom_stop_signal)
            except ValueError:
                error = (
                    f"py3status.stop_signal '{custom_stop_signal}' is invalid "
                    f"and should be a number between 0 (disable) and 31"
                )
                logger.error(error)
                raise Exception(error)

        # SIGTSTP can be received and indicates that all output should
        # stop and we should consider py3status suspended.  It is however
        # important that any processes using i3 ipc should continue to receive
        # those events otherwise it can lead to a stall in i3.
        signal(SIGTSTP, self.i3bar_stop)
        # SIGCONT indicates output should be resumed.
        signal(SIGCONT, self.i3bar_start)

        # get the list of py3status configured modules
        self.py3_modules = self.config["py3_config"]["py3_modules"]

        # print available modules
        # logger.debug("default modules: %s", self._get_default_modules())
        logger.info("path-included module paths: %s", list(map(str, self.config["include_paths"])))
        logger.debug("path-included modules: %s", list(self._get_path_included_modules()))
        logger.debug("entry-point modules: %s", self._get_entry_point_debug_modules())

        # get a dict of all configured discoverable modules
        discoverable_modules = self.get_configured_discoverable_modules()
        if self.py3_modules:
            # load and spawn i3status.conf configured modules threads
            self.load_modules(self.py3_modules, discoverable_modules)

        # determine the target output format
        self.output_format = OutputFormat.instance_for(
            self.config["py3_config"]["general"]["output_format"]
        )

        # determine the output separator, if needed
        color_separator = None
        if self.config["py3_config"]["general"]["colors"]:
            color_separator = self.config["py3_config"]["general"]["color_separator"]
        self.output_format.format_separator(
            self.config["py3_config"]["general"].get("separator", None),
            color_separator,
        )

    def notify_user(
        self,
        msg,
        level="error",
        rate_limit=None,
        module_name="",
        icon=None,
        title="py3status",
    ):
        """
        Display notification to user via i3-nagbar or send-notify
        We also make sure to log anything to keep trace of it.

        NOTE: Message should end with a '.' for consistency.
        """
        dbus = self.config.get("dbus_notify")
        if dbus:
            # force msg, icon, title to be a string
            title = f"{title}"
            msg = f"{msg}"
            if icon:
                icon = f"{icon}"
        else:
            msg = f"py3status: {msg}"
        if level != "info" and module_name == "":
            fix_msg = "{} Please try to fix this and reload i3wm (Mod+Shift+R)"
            msg = fix_msg.format(msg)
        # Rate limiting. If rate limiting then we need to calculate the time
        # period for which the message should not be repeated.  We just use
        # A simple chunked time model where a message cannot be repeated in a
        # given time period. Messages can be repeated more frequently but must
        # be in different time periods.

        limit_key = ""
        if rate_limit:
            try:
                limit_key = time.monotonic() // rate_limit
            except TypeError:
                pass
        # We use a hash to see if the message is being repeated.  This is crude
        # and imperfect but should work for our needs.
        msg_hash = hash(f"{module_name}#{limit_key}#{msg}#{title}")
        if msg_hash in self.notified_messages:
            return
        log_level = resolve_log_level(level)
        if module_name:
            notification_logger = logging.getLogger(module_logger_name(module_name))
            notification_logger.log(log_level, "notification: '%s: %s'", title, msg)
        else:
            logger.log(log_level, msg)
        self.notified_messages.add(msg_hash)

        try:
            if dbus:
                # fix any html entities
                msg = msg.replace("&", "&amp;")
                msg = msg.replace("<", "&lt;")
                msg = msg.replace(">", "&gt;")
                cmd = ["notify-send"]
                if icon:
                    cmd += ["-i", icon]
                cmd += ["-u", DBUS_LEVELS.get(level, "normal"), "-t", "10000"]
                cmd += [title, msg]
            else:
                py3_config = self.config.get("py3_config", {})
                nagbar_font = py3_config.get("py3status", {}).get("nagbar_font")
                wm_nag = self.config["wm"]["nag"]
                cmd = [wm_nag, "-m", msg, "-t", level]
                if nagbar_font:
                    cmd += ["-f", nagbar_font]
            Popen(
                cmd,
                stdout=Path("/dev/null").open("w"),
                stderr=Path("/dev/null").open("w"),
            )
        except Exception as err:
            logger.error("notify_user: %s", err)

    def stop(self):
        """
        Set the Event lock, this will break all threads' loops.
        """
        self.running = False
        # stop the command server
        try:
            self.commands_thread.kill()
        except:  # noqa e722
            pass

        try:
            self.lock.set()
            logger.debug("lock set, exiting")
            # run kill() method on all py3status modules
            for module in self.modules.values():
                module.kill()
        except:  # noqa e722
            pass

    def i3status_containers(self):
        """
        Every live i3status container module (generated or configured) -
        there can be several of these, each running its own subprocess.
        """
        for name, module in self.modules.items():
            if is_i3status_container_name(name):
                yield module.module_class

    def refresh_modules(self, module_string=None, exact=True):
        """
        Update modules.
        if module_string is None all modules are refreshed
        if module_string then modules with the exact name or those starting
        with the given string depending on exact parameter will be refreshed.
        If a module is an i3status container or proxy, its owning
        container's subprocess is refreshed too.
        To prevent abuse, we rate limit this function to 100ms for full
        refreshes.
        """
        if not module_string:
            if time.monotonic() > (self.last_refresh_ts + 0.1):
                self.last_refresh_ts = time.monotonic()
            else:
                # rate limiting
                return
        i3status_container_names = set()
        for name, module in self.output_modules.items():
            if (
                module_string is None
                or (exact and name == module_string)
                or (not exact and name.startswith(module_string))
            ):
                if is_i3status_proxy_name(name):
                    logger.debug("refreshing i3status module '%s'", name)
                    i3status_container_names.add(module["module"].module_class._container)
                elif is_i3status_container_name(name):
                    logger.debug("refreshing i3status module '%s'", name)
                    i3status_container_names.add(name)
                else:
                    logger.debug("refreshing py3status module '%s'", name)
                module["module"].force_update()
        # send SIGUSR1 only to i3status containers owning a just-refreshed proxy/container
        for i3status_container in self.i3status_containers():
            if i3status_container._module_full_name in i3status_container_names:
                i3status_container._refresh()

    def sig_handler(self, signum, frame):
        """
        SIGUSR1 was received, the user asks for an immediate refresh of the bar
        """
        logger.info("received USR1")
        self.refresh_modules()

    def terminate(self, signum, frame):
        """
        Received request to terminate (SIGTERM), exit nicely.
        """
        logger.info("received SIGTERM")
        raise KeyboardInterrupt()

    def purge_module(self, module_name):
        """
        A module has been removed e.g. a module that had an error.
        We need to find any containers and remove the module from them.

        No-op for an i3status container - it's not a real container
        (its items are raw i3status.conf dicts, not module names), so
        there's nothing here to remove it from.
        """
        containers = self.config["py3_config"][".module_groups"]
        containers_to_update = set()
        if module_name in containers:
            containers_to_update.update(set(containers[module_name]))
        for container in containers_to_update:
            try:
                self.modules[container].module_class.items.remove(module_name)
            except ValueError:
                pass

    def notify_update(self, update, urgent=False):
        """
        Name or list of names of modules that have updated.
        """
        if not isinstance(update, list):
            update = [update]
        self.update_queue.extend(update)

        # find containers that use the modules that updated
        containers = self.config["py3_config"][".module_groups"]
        containers_to_update = set()
        for item in update:
            if item in containers:
                containers_to_update.update(set(containers[item]))
        # force containers to update
        for container in containers_to_update:
            container_module = self.output_modules.get(container)
            if container_module:
                # If the container registered a urgent_function then call it
                # if this update is urgent.
                if urgent and container_module.get("urgent_function"):
                    container_module["urgent_function"](update)
                # If a container has registered a content_function we use that
                # to see if the container needs to be updated.
                # We only need to update containers if their active content has
                # changed.
                if container_module.get("content_function"):
                    if set(update) & container_module["content_function"]():
                        container_module["module"].force_update()
                else:
                    # we don't know so just update.
                    container_module["module"].force_update()

        # we need to update the output
        if self.update_queue:
            self.update_request.set()

    def create_output_modules(self):
        """
        Setup our output modules to allow easy updating of modules, allows
        the same module to be used multiple times.
        """
        py3_config = self.config["py3_config"]
        output_modules = self.output_modules
        # position in the bar of the modules
        positions = {}
        for index, name in enumerate(py3_config["order"]):
            if name not in positions:
                positions[name] = []
            positions[name].append(index)

        # py3status modules - includes i3status containers/proxies, which
        # are real Modules too now, not a separate i3status module type
        for name in self.modules:
            if name not in output_modules:
                output_modules[name] = {}
                output_modules[name]["position"] = positions.get(name, [])
                output_modules[name]["module"] = self.modules[name]
                output_modules[name]["color"] = self.mappings_color.get(name)

        self.output_modules = output_modules

    def create_mappings(self, config):
        """
        Create any mappings needed for global substitutions eg. colors
        """
        mappings = {}
        for name, cfg in config.items():
            # Ignore special config sections.
            if name in CONFIG_SPECIAL_SECTIONS:
                continue
            color = self.get_config_attribute(name, "color")
            if hasattr(color, "none_setting"):
                color = None
            mappings[name] = color
        # Store mappings for later use.
        self.mappings_color = mappings

    def process_module_output(self, module):
        """
        Process the output for a module and return a json string representing it.
        Color processing occurs here.
        """
        outputs = module["module"].get_latest()
        if self.config["py3_config"]["general"].get("colors") is False:
            for output in outputs:
                output.pop("color", None)
        else:
            color = module["color"]
            if color:
                for output in outputs:
                    # Color: substitute the config defined color
                    if "color" not in output:
                        output["color"] = color
        # format output and return
        return self.output_format.format(outputs)

    def i3bar_stop(self, signum, frame):
        if self.next_allowed_signal == signum and time.monotonic() > self.inhibit_signal_ts:
            logger.info("received stop_signal %s", Signals(signum).name)
            self.i3bar_running = False
            for i3status_container in self.i3status_containers():
                i3status_container._suspend()
            self.sleep_modules()
            self.next_allowed_signal = SIGCONT
        else:
            logger.warning("inhibited stop_signal %s", Signals(signum).name)
            self.inhibit_signal_ts = time.monotonic() + 0.1

    def i3bar_start(self, signum, frame):
        if self.next_allowed_signal == signum and time.monotonic() > self.inhibit_signal_ts:
            logger.info("received resume signal %s", Signals(signum).name)
            self.i3bar_running = True
            for i3status_container in self.i3status_containers():
                i3status_container._resume()
            self.wake_modules()
            self.next_allowed_signal = self.stop_signal
        else:
            logger.warning("inhibited start_signal %s", Signals(signum).name)
            self.inhibit_signal_ts = time.monotonic() + 0.1

    def sleep_modules(self):
        # Put all py3modules to sleep so they stop updating
        for module in self.output_modules.values():
            module["module"].sleep()

    def wake_modules(self):
        # Wake up all py3modules.
        for module in self.output_modules.values():
            module["module"].wake()

    @profile
    def run(self):
        """
        Main py3status loop, continuously read from modules (i3status included,
        as a regular module) and output it to i3bar for displaying.
        """
        # SIGUSR1 forces a refresh of the bar both for py3status and i3status,
        # this mimics the USR1 signal handling of i3status (see man i3status)
        signal(SIGUSR1, self.sig_handler)
        signal(SIGTERM, self.terminate)

        # initialize usage variables
        py3_config = self.config["py3_config"]

        # prepare the color mappings
        self.create_mappings(py3_config)

        # self.output_modules needs to have been created before modules are
        # started.  This is so that modules can do things like register their
        # content_function.
        self.create_output_modules()

        # start up all our modules
        for module in self.modules.values():
            task = ModuleRunner(module)
            self.timeout_queue_add(task)

        # this will be our output set to the correct length for the number of
        # items in the bar
        output = [None] * len(py3_config["order"])

        # start our output
        header = {
            "version": 1,
            "click_events": self.config["click_events"],
            "stop_signal": self.stop_signal or 0,
        }
        self.output_format.write_header(header)

        update_due = None
        # main loop
        while True:
            # process the timeout_queue and get interval till next update due
            update_due = self.timeout_queue_process()

            # wait until an update is requested
            if self.update_request.wait(timeout=update_due):
                # event was set so clear it
                self.update_request.clear()

            while not self.i3bar_running:
                time.sleep(0.1)

            # check if an update is needed
            if self.update_queue:
                while len(self.update_queue):
                    module_name = self.update_queue.popleft()
                    module = self.output_modules[module_name]
                    out = self.process_module_output(module)

                    for index in module["position"]:
                        # store the output as json
                        output[index] = out

                # build output string and dump to stdout
                self.output_format.write_line(output)
