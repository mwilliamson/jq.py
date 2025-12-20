import io
import json
import threading

from cpython.bytes cimport PyBytes_AsString
from cpython.bytes cimport PyBytes_AsStringAndSize
from libc.float cimport DBL_MAX
from libc.math cimport INFINITY, modf
