import base64
import inspect


class Private(object):
    """
    This class attempts to keep private information.

    Clearly this is python so we cannot actually achieve that aim.
    Any attacker could easily monkey patch out any of this code rendering it
    useless.

    The point of this is to make the code less likely to leak sensitive
    information for example via the logs, user notifications, displaying in
    i3bar.

    THIS IS NOT SECURE!
    """

    def __init__(self, encoded, module_name):
        self._decoded = False
        self._encoded = encoded
        self._module_name = module_name.split(" ")[0]
        self._private = u"***"  # this is used when the user is untrusted
        self._value = u"encrypted"

        # Try to decrypt data if possible
        self._decrypt()

    def _decrypt(self, key=None):
        """
        method called to decrypt the value
        """
        if not self._decoded:
            self._decode(key)

    def __setattr__(self, name, value):
        """
        Do not allow this object to be updated outside of this module
        """
        stack = inspect.stack()
        if inspect.getmodule(stack[1][0]).__name__ != __name__:
            return
        return object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        """
        Check if user can access this attribute.
        """
        # allowed by all users
        if name in ["_decrypt", "_decode"]:
            return object.__getattribute__(self, name)

        # allow internal calls
        stack = inspect.stack()
        state = (not name.startswith("_")) or (
            inspect.getmodule(stack[1][0]).__name__ == __name__
            and stack[1][3] in ["_catch", "_decode"]
        )
        if state:
            return object.__getattribute__(self, name)
        return None


def catch_factory(attr):
    """
    Factory returning a catch function
    """

    def _catch(s, *args, **kw):
        """
        This is used to catch and process all calls.
        """

        def process(value):
            """
            return the actual value after processing
            """
            if attr.startswith("__"):
                # __repr__, __str__ etc
                return getattr(value, attr)(*args, **kw)
            else:
                # upper, lower etc
                return getattr(u"".__class__, attr)(value, *args, **kw)

        stack = inspect.stack()
        mod = inspect.getmodule(stack[1][0])
        # We are called from the owning module so allow
        if mod.__name__.split(".")[-1] == s._module_name:
            return process(s._value)
        # very shallow calling no stack
        if len(stack) < 3:
            return process(s._private)
        # Check if this is an internal or external module.  We need to allow
        # calls to modules like requests etc
        remote = not inspect.getmodule(stack[2][0]).__name__.startswith("py3status")
        valid = False
        # go through the stack to see how we came through the code
        for frame in stack[2:]:
            mod = inspect.getmodule(frame[0])
            if remote and mod.__name__.split(".")[-1] == s._module_name:
                # the call to an external module started in the correct module
                # so allow this usage
                valid = True
                break
            if mod.__name__ == "py3status.py3" and frame[3] == "request":
                # Py3.request has special needs due so it is allowed to access
                # private variables.
                valid = True
                break
            if mod.__name__.startswith("py3status"):
                # We were somewhere else in py3status than the module, maybe we
                # are doing some logging.  Prevent usage
                return process(s._private)
        if valid:
            return process(s._value)
        return process(s._private)

    return _catch


# We need to populate our base class with all the methods that unicode
# has.  We will implement them using the _catch function created by out
# factory.  We want to exclude a few select methods
EXCLUDE = [
    "__init__",
    "__getattribute__",
    "__new__",
    "__setattr__",
    "__init_subclass__",
]
for attr in dir(u""):
    if attr.startswith("__") and attr in EXCLUDE:
        continue
    if "__call__" in dir(getattr(u"", attr)):
        setattr(Private, attr, catch_factory(attr))


class PrivateBase64(Private):
    """
    Simple base64 encoder
    """

    def _decode(self, key):
        if self._encoded is None:
            return
        try:
            new_value = base64.b64decode(self._encoded)
            self._value = new_value.decode("utf-8")
        except Exception:
            self._value = "Error"
        self._decoded = True


class PrivateHide(Private):
    """
    This does not encode the data in any way but it does keep it from being
    shown in the log files, i3bar etc
    """

    def _decode(self, key):
        if self._encoded is None:
            return
        self._value = self._encoded
        self._decoded = True


if __name__ == "__main__":
    # This module can read this
    x = PrivateHide("test", "__main__")
    print(x)
    print(x.upper())
    print(x.split("e"))
    # This module cannot read this
    x = PrivateHide("test", "xxx")
    print(x)
    print(x.upper())
    print(x.split("e"))
