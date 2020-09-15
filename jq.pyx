import json
import threading

from cpython.bytes cimport PyBytes_AsString
from cpython.bytes cimport PyBytes_AsStringAndSize


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
    int jv_is_integer(jv)
    double jv_number_value(jv)
    int jv_array_length(jv)
    jv jv_array_get(jv, int)
    int jv_object_iter(jv)
    int jv_object_iter_next(jv, int)
    int jv_object_iter_valid(jv, int)
    jv jv_object_iter_key(jv, int)
    jv jv_object_iter_value(jv, int)
    jv jv_invalid()

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

    if kind == JV_KIND_INVALID:
        raise ValueError("Invalid value")
    elif kind == JV_KIND_NULL:
        python_value = None
    elif kind == JV_KIND_FALSE:
        python_value = False
    elif kind == JV_KIND_TRUE:
        python_value = True
    elif kind == JV_KIND_NUMBER:
        if jv_is_integer(value):
            python_value = int(jv_number_value(value))
        else:
            python_value = float(jv_number_value(value))
    elif kind == JV_KIND_STRING:
        python_value = jv_string_value(value).decode("utf-8")
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
                python_value[jv_string_value(property_key).decode("utf-8")] = \
                    _jv_to_python(property_value)
            finally:
                jv_free(property_key)
            idx = jv_object_iter_next(value, idx)
    else:
        raise ValueError("Invalid value kind: " + str(kind))
    jv_free(value)
    return python_value


class JSONParseError(Exception):
    """A failure to parse JSON"""


cdef class _JV(object):
    """Native JSON value"""
    cdef jv _value

    def __dealloc__(self):
        jv_free(self._value)

    def __cinit__(self):
        self._value = jv_invalid()

    def unpack(self):
        """
        Unpack the JSON value into standard Python representation.

        Returns:
            An unpacked copy of the JSON value.
        """
        return _jv_to_python(jv_copy(self._value))


cdef class _JSONParser(object):
    cdef jv_parser* _parser
    cdef object _text_iter
    cdef object _bytes
    cdef int _packed

    def __dealloc__(self):
        jv_parser_free(self._parser)

    def __cinit__(self, text_iter, packed):
        """
        Initialize the parser.

        Args:
            text_iter:  An iterator producing pieces of the JSON stream text
                        (strings or bytes) to parse.
            packed:     Make the iterator return jq-native packed values,
                        if true, and standard Python values, if false.
        """
        self._parser = jv_parser_new(0)
        self._text_iter = text_iter
        self._bytes = None
        self._packed = bool(packed)

    def __iter__(self):
        return self

    def __next__(self):
        """
        Retrieve next parsed JSON value.

        Returns:
            The next parsed JSON value.

        Raises:
            JSONParseError: failed parsing the input JSON.
            StopIteration: no more values available.
        """
        cdef jv value
        while True:
            # If we have no bytes to parse
            if self._bytes is None:
                # Ready some more
                self._ready_next_bytes()
            # Parse whatever we've readied, if any
            value = jv_parser_next(self._parser)
            if jv_is_valid(value):
                if self._packed:
                    packed = _JV()
                    packed._value = value
                    return packed
                else:
                    return _jv_to_python(value)
            elif jv_invalid_has_msg(jv_copy(value)):
                error_message = jv_invalid_get_msg(value)
                message = jv_string_value(error_message).decode("utf8")
                jv_free(error_message)
                raise JSONParseError(message)
            else:
                jv_free(value)
                # If we didn't ready any bytes
                if self._bytes is None:
                    raise StopIteration
                self._bytes = None

    cdef bint _ready_next_bytes(self) except 1:
        cdef char* cbytes
        cdef ssize_t clen
        try:
            text = next(self._text_iter)
            if isinstance(text, bytes):
                self._bytes = text
            else:
                self._bytes = text.encode("utf8")
            PyBytes_AsStringAndSize(self._bytes, &cbytes, &clen)
            jv_parser_set_buf(self._parser, cbytes, clen, 1)
        except StopIteration:
            self._bytes = None
            jv_parser_set_buf(self._parser, "", 0, 0)
        return 0


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
        cdef char* cbytes_input
        cdef ssize_t clen_input
        PyBytes_AsStringAndSize(bytes_input, &cbytes_input, &clen_input)
        jv_parser_set_buf(parser, cbytes_input, clen_input, 0)
        self._parser = parser

    def __iter__(self):
        return self

    def __next__(self):
        cdef int dumpopts = 0
        while True:
            if not self._ready:
                self._ready_next_input()
                self._ready = True

            result = jq_next(self._jq)
            if jv_is_valid(result):
                return _jv_to_python(result)
            elif jv_invalid_has_msg(jv_copy(result)):
                error_message = jv_invalid_get_msg(result)
                message = jv_string_value(error_message).decode("utf8")
                jv_free(error_message)
                raise ValueError(message)
            else:
                jv_free(result)
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


def parse_json(text=_NO_VALUE, text_iter=_NO_VALUE, packed=False):
    """
    Parse a JSON stream.
    Either "text" or "text_iter" must be specified.

    Args:
        text:       A string or bytes object containing the JSON stream to
                    parse.
        text_iter:  An iterator returning strings or bytes - pieces of the
                    JSON stream to parse.
        packed:     If true, return packed, jq-native JSON values.
                    If false, return standard Python JSON values.

    Returns:
        An iterator returning parsed values.

    Raises:
        JSONParseError: failed parsing the input JSON stream.
    """
    if (text is _NO_VALUE) == (text_iter is _NO_VALUE):
        raise ValueError("Either the text or text_iter argument should be set")
    return _JSONParser(text_iter
                       if text_iter is not _NO_VALUE
                       else _iter((text,)),
                       packed)


def parse_json_file(fp, packed=False):
    """
    Parse a JSON stream file.

    Args:
        fp: The file-like object to read the JSON stream from.
        packed: If true, return packed, jq-native JSON values.
                If false, return standard Python JSON values.

    Returns:
        An iterator returning parsed values.

    Raises:
        JSONParseError: failed parsing the JSON stream.
    """
    return parse_json(text=fp.read(), packed=packed)


# Support the 0.1.x API for backwards compatibility
def jq(object program):
    return compile(program)
