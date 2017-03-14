class Py3Exception(Exception):
    """
    Base Py3 exception class.  All custom Py3 exceptions derive from this
    class.
    """


class RequestException(Py3Exception):
    """
    A Py3.request() base exception.  This will catch any of the more specific
    exceptions.
    """


class RequestTimeout(RequestException):
    """
    A timeout has occured during a request made via Py3.request().
    """


class RequestURLError(RequestException):
    """
    A URL related error has occured during a request made via Py3.request().
    """
