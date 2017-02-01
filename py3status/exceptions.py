class Py3Exception(Exception):
    """ Base exception class """


class RequestException(Py3Exception):
    """ A url request base exception """


class RequestTimeout(RequestException):
    """ A Timeout """


class RequestURLError(RequestException):
    """ A URL related error """
