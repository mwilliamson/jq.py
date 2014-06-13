import json


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
    

def jq(object program):
    cdef object program_bytes_obj = program.encode("utf8")
    cdef char* program_bytes = program_bytes_obj
    cdef jq_state *jq = jq_init()
    if not jq:
        raise Exception("jq_init failed")
    
    cdef _ErrorStore error_store = _ErrorStore.__new__(_ErrorStore)
    error_store.clear()
    
    jq_set_error_cb(jq, store_error, <void*>error_store)
    
    cdef int compiled = jq_compile(jq, program_bytes)
    
    if error_store.has_errors():
        raise ValueError(error_store.error_string())
    
    if not compiled:
        raise ValueError("program was not valid")
    
    cdef _Program wrapped_program = _Program.__new__(_Program)
    wrapped_program._jq = jq
    wrapped_program._error_store = error_store
    return wrapped_program


cdef void store_error(void* store_ptr, jv error):
    # TODO: handle errors not of JV_KIND_STRING
    cdef _ErrorStore store = <_ErrorStore>store_ptr
    if jv_get_kind(error) == JV_KIND_STRING:
        store.store_error(jv_string_value(error))


cdef class _ErrorStore(object):
    cdef object _errors
    
    cdef int has_errors(self):
        return len(self._errors)
    
    cdef object error_string(self):
        return "\n".join(self._errors)
    
    cdef void store_error(self, char* error):
        self._errors.append(error.decode("utf8"))
    
    cdef void clear(self):
        self._errors = []


class EmptyValue(object):
    pass

_NO_VALUE = EmptyValue()

cdef class _Program(object):
    cdef jq_state* _jq
    cdef _ErrorStore _error_store

    def __dealloc__(self):
        jq_teardown(&self._jq)
    
    def transform(self, value=_NO_VALUE, text=_NO_VALUE, text_output=False, multiple_output=False):
        if (value is _NO_VALUE) == (text is _NO_VALUE):
            raise ValueError("Either the value or text argument should be set")
        string_input = text if text is not _NO_VALUE else json.dumps(value)
        bytes_input = string_input.encode("utf8")
        
        self._error_store.clear()
        
        result_bytes = self._string_to_strings(bytes_input)
        
        if self._error_store.has_errors():
            raise ValueError(self._error_store.error_string())
        
        result_strings = map(lambda s: s.decode("utf8"), result_bytes)
        if text_output:
            return "\n".join(result_strings)
        elif multiple_output:
            return [json.loads(s) for s in result_strings]
        else:
            return json.loads(next(iter(result_strings)))

    cdef object _string_to_strings(self, char* input):
        cdef jv_parser* parser = jv_parser_new(0)
        jv_parser_set_buf(parser, input, len(input), 0)
        cdef jv value
        cdef jv error_message
        results = []
        while True:
            value = jv_parser_next(parser)
            if jv_is_valid(value):
                self._process(value, results)
            else:
                if jv_invalid_has_msg(jv_copy(value)):
                    error_message = jv_invalid_get_msg(value)
                    full_error_message = b"parse error: " + jv_string_value(error_message) + b"\n"
                    self._error_store.store_error(full_error_message)
                    jv_free(error_message)
                else:
                    jv_free(value)
                break
                
        jv_parser_free(parser)
        
        return results


    cdef void _process(self, jv value, object output):
        cdef int jq_flags = 0
        
        jq_start(self._jq, value, jq_flags);
        cdef jv result
        cdef int dumpopts = 0
        cdef jv dumped
        
        while True:
            result = jq_next(self._jq)
            if not jv_is_valid(result):
                jv_free(result)
                return
            else:
                dumped = jv_dump_string(result, dumpopts)
                output.append(jv_string_value(dumped))
                jv_free(dumped)
