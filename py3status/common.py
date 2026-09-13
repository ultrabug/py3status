import logging
import sys
from pathlib import Path
from traceback import extract_tb, format_stack, format_tb

from py3status.formatter import expand_color
from py3status.helpers import print_stderr
from py3status.log import resolve_log_level

logger = logging.getLogger(__name__)


class NoneSetting:
    """
    This class represents no setting in the config.
    """

    # this attribute is used to identify that this is a none setting
    none_setting = True

    def __len__(self):
        return 0

    def __repr__(self):
        # this is for output via module_test
        return "None"


class Common:
    """
    This class is used to hold core functionality so that it can be shared more
    easily.  This allow us to run the module tests through the same code as
    when we are running for real.
    """

    def __init__(self, py3_wrapper):
        self.py3_wrapper = py3_wrapper
        self.none_setting = NoneSetting()
        self.config = py3_wrapper.config

    def get_config_attribute(self, name, attribute):
        """
        Look for the attribute in the config.  Start with the named module and
        then walk up through any containing group and then try the general
        section of the config.
        """

        # A user can set a param to None in the config to prevent a param
        # being used.  This is important when modules do something like
        #
        # color = self.py3.COLOR_MUTED or self.py3.COLOR_BAD
        config = self.config["py3_config"]
        param = config[name].get(attribute, self.none_setting)
        if hasattr(param, "none_setting") and name in config[".module_groups"]:
            for module in config[".module_groups"][name]:
                if attribute in config.get(module, {}):
                    param = config[module].get(attribute)
                    break
        if hasattr(param, "none_setting"):
            # check py3status config section
            param = config["py3status"].get(attribute, self.none_setting)
        if hasattr(param, "none_setting"):
            # check py3status general section
            param = config["general"].get(attribute, self.none_setting)
        if param and (attribute == "color" or attribute.startswith("color_")):
            # check color value
            param = expand_color(param.lower(), self.none_setting)
        return param

    def report_exception(self, msg, notify_user=True, level="error", error_frame=None, name=None):
        """
        Report details of an exception to the user.
        This should only be called within an except: block Details of the
        exception are reported eg filename, line number and exception type.

        Because stack trace information outside of py3status or it's modules is
        not helpful in actually finding and fixing the error, we try to locate
        the first place that the exception affected our code.

        Alternatively if the error occurs in a module via a Py3 call that
        catches and reports the error then we receive an error_frame and use
        that as the source of the error.

        NOTE: msg should not end in a '.' for consistency.
        """
        # Get list of paths that our stack trace should be found in.
        py3_paths = [Path(__file__).resolve().parent] + self.config["include_paths"]
        traceback = None

        try:
            # We need to make sure to delete tb even if things go wrong.
            exc_type, exc_obj, tb = sys.exc_info()
            stack = extract_tb(tb)
            error_str = f"{exc_type.__name__}: {exc_obj}\n"
            traceback = [error_str]

            if error_frame:
                # The error occurred in a py3status module so the traceback
                # should be made to appear correct.  We caught the exception
                # but make it look as though we did not.
                traceback += format_stack(error_frame, 1) + format_tb(tb)
                filename = Path(error_frame.f_code.co_filename).name
                line_no = error_frame.f_lineno
            else:
                # This is a none module based error
                traceback += format_tb(tb)
                # Find first relevant trace in the stack.
                # it should be in py3status or one of it's modules.
                found = False
                for item in reversed(stack):
                    filename = item[0]
                    for path in py3_paths:
                        if filename.startswith(str(path)):
                            # Found a good trace
                            filename = Path(item[0]).name
                            line_no = item[1]
                            found = True
                            break
                    if found:
                        break
            # all done!  create our message.
            msg = "{} ({}) {} line {}".format(msg, exc_type.__name__, filename, line_no)
        except Exception:
            # something went wrong, report msg as-is.
            pass
        finally:
            # delete tb!
            del tb
        # log the exception and notify user
        tmp_logger = logging.getLogger(name) if name else logger
        tmp_logger.log(resolve_log_level(level), msg)
        if traceback:
            # if debug is not in the config  then we are at an early stage of
            # running py3status and logging is not yet available so output the
            # error to STDERR so it can be seen
            if "debug" not in self.config:
                print_stderr("\n".join(traceback))
            elif self.config.get("log_file"):
                tmp_logger.info("traceback\n%s", "".join(traceback))
        if notify_user:
            self.py3_wrapper.notify_user(msg, level=level)
