import io
import json
import threading

from cpython.bytes cimport PyBytes_AsString
from cpython.bytes cimport PyBytes_AsStringAndSize
from libc.float cimport DBL_MAX
from libc.math cimport INFINITY, modf


cdef extern from "jv.h":
    ctypedef enum jv_kind:
      JV_KIND_INVALID,
      JV_KIND_NULL,
      JV_KIND_FALSE,
      JV_KIND_TRUE,
      JV_KIND_NUMBER,
      JV_KIND_STRING,
      JV_KIND_ARRAY,
      JV_KIND_OBJECT

    ctypedef struct jv:
        pass

    jv_kind jv_get_kind(jv)
    int jv_is_valid(jv)
    jv jv_copy(jv)
    void jv_free(jv)
    jv jv_invalid_get_msg(jv)
    int jv_invalid_has_msg(jv)
    char* jv_string_value(jv)
    jv jv_dump_string(jv, int flags)
    int jv_string_length_bytes(jv)
    int jv_is_integer(jv)
    double jv_number_value(jv)
    jv jv_array()
    jv jv_array_append(jv, jv)
    int jv_array_length(jv)
    jv jv_array_get(jv, int)
    int jv_object_iter(jv)
    int jv_object_iter_next(jv, int)
    int jv_object_iter_valid(jv, int)
    jv jv_object_iter_key(jv, int)
    jv jv_object_iter_value(jv, int)

    cdef struct jv_parser:
        pass

    jv_parser* jv_parser_new(int)
    void jv_parser_free(jv_parser*)
    void jv_parser_set_buf(jv_parser*, const char*, int, int)
    jv jv_parser_next(jv_parser*)

    jv jv_parse(const char*)


cdef extern from "jq.h":
    ctypedef struct jq_state:
        pass

    ctypedef void (*jq_err_cb)(void *, jv)

    jq_state *jq_init()
    void jq_teardown(jq_state **)
    int jq_compile(jq_state *, const char* str)
    int jq_compile_args(jq_state *, const char* str, jv)
    void jq_start(jq_state *, jv value, int flags)
    jv jq_next(jq_state *)
    void jq_set_error_cb(jq_state *, jq_err_cb, void *)
    void jq_get_error_cb(jq_state *, jq_err_cb *, void **)


cdef object _jv_to_python(jv value):
    """Unpack a jv value into a Python value"""
    cdef jv_kind kind = jv_get_kind(value)
    cdef int idx
    cdef jv property_key
    cdef jv property_value
    cdef object python_value
    cdef double number_value

    if kind == JV_KIND_INVALID:
        raise ValueError("Invalid value")
    elif kind == JV_KIND_NULL:
        python_value = None
    elif kind == JV_KIND_FALSE:
        python_value = False
    elif kind == JV_KIND_TRUE:
        python_value = True
    elif kind == JV_KIND_NUMBER:
        number_value = jv_number_value(value)
        if number_value == INFINITY:
            python_value = DBL_MAX
        elif number_value == -INFINITY:
            python_value = -DBL_MAX
        elif number_value != number_value:
            python_value = None
        elif _is_integer(number_value):
            python_value = int(number_value)
        else:
            python_value = number_value
    elif kind == JV_KIND_STRING:
        python_value = jv_string_to_py_string(value)
    elif kind == JV_KIND_ARRAY:
        python_value = []
        for idx in range(0, jv_array_length(jv_copy(value))):
            property_value = jv_array_get(jv_copy(value), idx)
            python_value.append(_jv_to_python(property_value))
    elif kind == JV_KIND_OBJECT:
        python_value = {}
        idx = jv_object_iter(value)
        while jv_object_iter_valid(value, idx):
            property_key = jv_object_iter_key(value, idx)
            property_value = jv_object_iter_value(value, idx)
            try:
                python_value[jv_string_to_py_string(property_key)] = \
                    _jv_to_python(property_value)
            finally:
                jv_free(property_key)
            idx = jv_object_iter_next(value, idx)
    else:
        raise ValueError("Invalid value kind: " + str(kind))
    jv_free(value)
    return python_value


cdef int _is_integer(double value) noexcept:
    cdef double integral_part
    cdef double fractional_part = modf(value, &integral_part)

    return fractional_part == 0


def compile(object program, args=None):
    cdef object program_bytes = program.encode("utf8")
    return _Program(program_bytes, args=args)


_compilation_lock = threading.Lock()


cdef jq_state* _compile(object program_bytes, object args) except NULL:
    cdef jq_state *jq = jq_init()
    cdef _ErrorStore error_store
    cdef jv jv_args
    cdef int compiled
    try:
        if not jq:
            raise Exception("jq_init failed")

        error_store = _ErrorStore()

        with _compilation_lock:
            jq_set_error_cb(jq, _store_error, <void*>error_store)

            if args is None:
                compiled = jq_compile(jq, program_bytes)
            else:
                args_bytes = json.dumps(args).encode("utf-8")
                jv_args = jv_parse(PyBytes_AsString(args_bytes))
                compiled = jq_compile_args(jq, program_bytes, jv_args)

            if error_store.has_errors():
                raise ValueError(error_store.error_string())

        if not compiled:
            raise ValueError("program was not valid")
    except:
        jq_teardown(&jq)
        raise
    # TODO: unset error callback?

    return jq


cdef void _store_error(void* store_ptr, jv error) noexcept:
    cdef _ErrorStore store = <_ErrorStore>store_ptr

    error_string = _jq_error_to_py_string(error)
    store.store_error(error_string)

    jv_free(error)


cdef unicode _jq_error_to_py_string(jv error) noexcept:
    error = jv_copy(error)

    if jv_get_kind(error) == JV_KIND_STRING:
        try:
            return jv_string_to_py_string(error)
        except:
            return u"Internal error"
    else:
        return json.dumps(_jv_to_python(error))


cdef class _ErrorStore(object):
    cdef object _errors

    def __cinit__(self):
        self.clear()

    cdef int has_errors(self):
        return len(self._errors)

    cdef object error_string(self):
        return "\n".join(self._errors)

    cdef void store_error(self, unicode error):
        self._errors.append(error)

    cdef void clear(self):
        self._errors = []


class _EmptyValue(object):
    pass

_NO_VALUE = _EmptyValue()


cdef class _JqStatePool(object):
    cdef jq_state* _jq_state
    cdef object _program_bytes
    cdef object _args
    cdef object _lock

    def __cinit__(self, program_bytes, args):
        self._program_bytes = program_bytes
        self._args = args
        self._jq_state = _compile(self._program_bytes, args=self._args)
        self._lock = threading.Lock()

    def __dealloc__(self):
        jq_teardown(&self._jq_state)

    cdef jq_state* acquire(self):
        with self._lock:
            if self._jq_state == NULL:
                return _compile(self._program_bytes, args=self._args)
            else:
                state = self._jq_state
                self._jq_state = NULL
                return state

    cdef void release(self, jq_state* state):
        with self._lock:
            if self._jq_state == NULL:
                self._jq_state = state
            else:
                jq_teardown(&state)


cdef class _Program(object):
    cdef object _program_bytes
    cdef _JqStatePool _jq_state_pool

    def __cinit__(self, program_bytes, args):
        self._program_bytes = program_bytes
        self._jq_state_pool = _JqStatePool(program_bytes, args=args)

    def input(self, value=_NO_VALUE, text=_NO_VALUE):
        if (value is _NO_VALUE) == (text is _NO_VALUE):
            raise ValueError("Either the value or text argument should be set")

        if text is not _NO_VALUE:
            return self.input_text(text)
        else:
            return self.input_value(value)

    def input_value(self, value):
        return self.input_text(json.dumps(value))

    def input_values(self, values):
        fileobj = io.StringIO()
        for value in values:
            json.dump(value, fileobj)
            fileobj.write("\n")
        return self.input_text(fileobj.getvalue())

    def input_text(self, text, *, slurp=False):
        return _ProgramWithInput(self._jq_state_pool, text.encode("utf8"), slurp=slurp)

    @property
    def program_string(self):
        return self._program_bytes.decode("utf8")

    def __repr__(self):
        return "jq.compile({!r})".format(self.program_string)

    # Support the 0.1.x API for backwards compatibility
    def transform(self, value=_NO_VALUE, text=_NO_VALUE, text_output=False, multiple_output=False):
        program_with_input = self.input(value, text=text)
        if text_output:
            return program_with_input.text()
        elif multiple_output:
            return program_with_input.all()
        else:
            return program_with_input.first()


cdef class _ProgramWithInput(object):
    cdef _JqStatePool _jq_state_pool
    cdef object _bytes_input
    cdef bint _slurp

    def __cinit__(self, jq_state_pool, bytes_input, *, bint slurp):
        self._jq_state_pool = jq_state_pool
        self._bytes_input = bytes_input
        self._slurp = slurp

    def __iter__(self):
        return self._make_iterator()

    cdef _ResultIterator _make_iterator(self):
        return _ResultIterator(self._jq_state_pool, self._bytes_input, slurp=self._slurp)

    def text(self):
        # Performance testing suggests that using _jv_to_python (within the
        # result iterator) followed by json.dumps is faster than using
        # jv_dump_string to generate the string directly from the jv values.
        # See: https://github.com/mwilliamson/jq.py/pull/50
        return "\n".join(json.dumps(v) for v in self)

    def all(self):
        return list(self)

    def first(self):
        return next(_iter(self))


cdef class _ResultIterator(object):
    cdef _JqStatePool _jq_state_pool
    cdef jq_state* _jq
    cdef jv_parser* _parser
    cdef bytes _bytes_input
    cdef bint _slurp
    cdef bint _ready

    def __dealloc__(self):
        self._jq_state_pool.release(self._jq)
        jv_parser_free(self._parser)

    def __cinit__(self, _JqStatePool jq_state_pool, bytes bytes_input, *, bint slurp):
        self._jq_state_pool = jq_state_pool
        self._jq = jq_state_pool.acquire()
        self._bytes_input = bytes_input
        self._slurp = slurp
        self._ready = False
        cdef jv_parser* parser = jv_parser_new(0)
        cdef char* cbytes_input
        cdef ssize_t clen_input
        PyBytes_AsStringAndSize(bytes_input, &cbytes_input, &clen_input)
        jv_parser_set_buf(parser, cbytes_input, clen_input, 0)
        self._parser = parser

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if not self._ready:
                self._ready_next_input()
                self._ready = True

            result = jq_next(self._jq)
            if jv_is_valid(result):
                return _jv_to_python(result)
            elif jv_invalid_has_msg(jv_copy(result)):
                error_message = jv_invalid_get_msg(result)
                message = _jq_error_to_py_string(error_message)
                jv_free(error_message)
                raise ValueError(message)
            else:
                jv_free(result)
                self._ready = False

    cdef bint _ready_next_input(self) except 1:
        cdef int jq_flags = 0
        cdef jv value

        if self._slurp:
            value = jv_array()

            while True:
                try:
                    next_value = self._parse_next_input()
                    value = jv_array_append(value, next_value)
                except StopIteration:
                    self._slurp = False
                    break
        else:
            value = self._parse_next_input()

        jq_start(self._jq, value, jq_flags)
        return 0

    cdef inline jv _parse_next_input(self) except *:
        cdef jv value = jv_parser_next(self._parser)
        if jv_is_valid(value):
            return value
        elif jv_invalid_has_msg(jv_copy(value)):
            error_message = jv_invalid_get_msg(value)
            message = _jq_error_to_py_string(error_message)
            jv_free(error_message)
            raise ValueError(u"parse error: " + message)
        else:
            jv_free(value)
            raise StopIteration()


def all(program, value=_NO_VALUE, text=_NO_VALUE):
    return compile(program).input(value, text=text).all()


def first(program, value=_NO_VALUE, text=_NO_VALUE):
    return compile(program).input(value, text=text).first()


_iter = iter


def iter(program, value=_NO_VALUE, text=_NO_VALUE):
    return _iter(compile(program).input(value, text=text))


def text(program, value=_NO_VALUE, text=_NO_VALUE):
    return compile(program).input(value, text=text).text()


# Support the 0.1.x API for backwards compatibility
def jq(object program):
    return compile(program)


cdef unicode jv_string_to_py_string(jv value):
    cdef int length = jv_string_length_bytes(jv_copy(value))
    cdef char* string_value = jv_string_value(value)
    return string_value[:length].decode("utf-8")
