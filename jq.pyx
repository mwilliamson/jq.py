import json


cdef extern from "jv.h":
    ctypedef struct jv:
        pass
    int jv_is_valid(jv)
    char* jv_string_value(jv)
    jv jv_dump_string(jv, int flags)
    void jv_free(jv)
    
    cdef struct jv_parser:
        pass
    
    jv_parser* jv_parser_new()
    void jv_parser_free(jv_parser*)
    void jv_parser_set_buf(jv_parser*, const char*, int, int)
    jv jv_parser_next(jv_parser*)


cdef extern from "jq.h":
    ctypedef struct jq_state:
        pass
        
    jq_state *jq_init()
    void jq_teardown(jq_state **)
    int jq_compile(jq_state *, const char* str)
    void jq_start(jq_state *, jv value, int flags)
    jv jq_next(jq_state *)
    

def jq(object program):
    cdef object program_bytes_obj = program.encode("utf8")
    cdef char* program_bytes = program_bytes_obj
    cdef jq_state *jq = jq_init()
    if not jq:
        raise Exception("jq_init failed")
    
    # TODO: jq_compile prints error to stderr
    cdef int compiled = jq_compile(jq, program_bytes)
    
    if not compiled:
        raise ValueError("program was not valid")
    
    cdef _Program wrapped_program = _Program.__new__(_Program)
    wrapped_program._jq = jq
    return wrapped_program


cdef class _Program(object):
    cdef jq_state* _jq

    def __dealloc__(self):
        jq_teardown(&self._jq)
    
    def transform(self, input, raw_input=False, raw_output=False, multiple_output=False):
        string_input = input if raw_input else json.dumps(input)
        bytes_input = string_input.encode("utf8")
        result_bytes = self._string_to_strings(bytes_input)
        result_strings = result_bytes
        if raw_output:
            return "\n".join(result_strings)
        elif multiple_output:
            return map(json.loads, result_strings)
        else:
            return json.loads(result_strings[0])
        

    cdef object _string_to_strings(self, char* input):
        cdef jv_parser* parser = jv_parser_new()
        jv_parser_set_buf(parser, input, len(input), 0)
        cdef jv value
        results = []
        while True:
            value = jv_parser_next(parser)
            if jv_is_valid(value):
                self._process(value, results)
            else:
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
