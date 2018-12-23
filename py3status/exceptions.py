class Py3Exception(Exception):
    """
    Base Py3 exception class.  All custom Py3 exceptions derive from this
    class.
    """


class CommandError(Py3Exception):
    """
    An error occurred running the given command.

    This exception provides some additional attributes

    ``error_code``: The error code returned from the call

    ``output``: Any output returned by the call

    ``error``: Any error output returned by the call
    """

    def __init__(self, msg=None, error_code=0, output="", error=""):
        Py3Exception.__init__(self, msg)
        self.error_code = error_code
        self.output = output
        self.error = error


class RequestException(Py3Exception):
    """
    A Py3.request() base exception.  This will catch any of the more specific
    exceptions.
    """


class RequestInvalidJSON(RequestException):
    """
    The request has not returned valid JSON
    """


class RequestTimeout(RequestException):
    """
    A timeout has occurred during a request made via Py3.request().
    """


class RequestURLError(RequestException):
    """
    A URL related error has occurred during a request made via Py3.request().
    """
