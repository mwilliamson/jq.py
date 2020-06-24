import json
import threading

from cpython.bytes cimport PyBytes_AsString


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

    cdef struct jv_parser:
        pass

    jv_parser* jv_parser_new(int)
    void jv_parser_free(jv_parser*)
    void jv_parser_set_buf(jv_parser*, const char*, int, int)
    jv jv_parser_next(jv_parser*)


cdef extern from "jq.h":
    ctypedef struct jq_state:
        pass

    ctypedef void (*jq_err_cb)(void *, jv)

    jq_state *jq_init()
    void jq_teardown(jq_state **)
    int jq_compile(jq_state *, const char* str)
    void jq_start(jq_state *, jv value, int flags)
    jv jq_next(jq_state *)
    void jq_set_error_cb(jq_state *, jq_err_cb, void *)
    void jq_get_error_cb(jq_state *, jq_err_cb *, void **)


def compile(object program):
    cdef object program_bytes = program.encode("utf8")
    return _Program(program_bytes)


cdef jq_state* _compile(object program_bytes) except NULL:
    cdef jq_state *jq = jq_init()
    cdef _ErrorStore error_store
    cdef int compiled
    try:
        if not jq:
            raise Exception("jq_init failed")

        error_store = _ErrorStore()

        jq_set_error_cb(jq, _store_error, <void*>error_store)

        compiled = jq_compile(jq, program_bytes)

        if error_store.has_errors():
            raise ValueError(error_store.error_string())

        if not compiled:
            raise ValueError("program was not valid")
    except:
        jq_teardown(&jq)
        raise
    # TODO: unset error callback?

    return jq


cdef void _store_error(void* store_ptr, jv error):
    # TODO: handle errors not of JV_KIND_STRING
    cdef _ErrorStore store = <_ErrorStore>store_ptr
    if jv_get_kind(error) == JV_KIND_STRING:
        store.store_error(jv_string_value(error).decode("utf8"))

    jv_free(error)


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
    cdef object _lock

    def __cinit__(self, program_bytes):
        self._program_bytes = program_bytes
        self._jq_state = _compile(self._program_bytes)
        self._lock = threading.Lock()

    def __dealloc__(self):
        jq_teardown(&self._jq_state)

    cdef jq_state* acquire(self):
        with self._lock:
            if self._jq_state == NULL:
                return _compile(self._program_bytes)
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

    def __cinit__(self, program_bytes):
        self._program_bytes = program_bytes
        self._jq_state_pool = _JqStatePool(program_bytes)

    def input(self, value=_NO_VALUE, text=_NO_VALUE):
        if (value is _NO_VALUE) == (text is _NO_VALUE):
            raise ValueError("Either the value or text argument should be set")
        string_input = text if text is not _NO_VALUE else json.dumps(value)

        return _ProgramWithInput(self._jq_state_pool, string_input.encode("utf8"))

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

    def __cinit__(self, jq_state_pool, bytes_input):
        self._jq_state_pool = jq_state_pool
        self._bytes_input = bytes_input

    def __iter__(self):
        return self._make_iterator()

    cdef _ResultIterator _make_iterator(self):
        return _ResultIterator(self._jq_state_pool, self._bytes_input)

    def text(self):
        iterator = self._make_iterator()
        results = []
        while True:
            try:
                results.append(iterator._next_string())
            except StopIteration:
                return "\n".join(results)

    def all(self):
        return list(self)

    def first(self):
        return next(_iter(self))


cdef class _ResultIterator(object):
    cdef _JqStatePool _jq_state_pool
    cdef jq_state* _jq
    cdef jv_parser* _parser
    cdef object _bytes_input
    cdef bint _ready

    def __dealloc__(self):
        self._jq_state_pool.release(self._jq)
        jv_parser_free(self._parser)

    def __cinit__(self, _JqStatePool jq_state_pool, object bytes_input):
        self._jq_state_pool = jq_state_pool
        self._jq = jq_state_pool.acquire()
        self._bytes_input = bytes_input
        self._ready = False
        cdef jv_parser* parser = jv_parser_new(0)
        cdef char* cbytes_input = PyBytes_AsString(bytes_input)
        jv_parser_set_buf(parser, cbytes_input, len(cbytes_input), 0)
        self._parser = parser

    def __iter__(self):
        return self

    def __next__(self):
        return json.loads(self._next_string())

    cdef unicode _next_string(self):
        cdef int dumpopts = 0
        while True:
            if not self._ready:
                self._ready_next_input()
                self._ready = True

            result = jq_next(self._jq)
            if jv_is_valid(result):
                dumped = jv_dump_string(result, dumpopts)
                value = jv_string_value(dumped).decode("utf8")
                jv_free(dumped)
                return value
            elif jv_invalid_has_msg(jv_copy(result)):
                error_message = jv_invalid_get_msg(result)
                message = jv_string_value(error_message).decode("utf8")
                jv_free(error_message)
                raise ValueError(message)
            else:
                self._ready = False

    cdef bint _ready_next_input(self) except 1:
        cdef int jq_flags = 0
        cdef jv value = jv_parser_next(self._parser)
        if jv_is_valid(value):
            jq_start(self._jq, value, jq_flags)
            return 0
        elif jv_invalid_has_msg(jv_copy(value)):
            error_message = jv_invalid_get_msg(value)
            message = jv_string_value(error_message).decode("utf8")
            jv_free(error_message)
            raise ValueError(u"parse error: " + message)
        else:
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
