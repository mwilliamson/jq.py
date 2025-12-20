import io
import json
import threading

from cpython.bytes cimport PyBytes_AsString
from cpython.bytes cimport PyBytes_AsStringAndSize
from libc.float cimport DBL_MAX
from libc.math cimport INFINITY, modf


_compilation_lock = threading.Lock()


class _EmptyValue(object):
    pass

_NO_VALUE = _EmptyValue()
