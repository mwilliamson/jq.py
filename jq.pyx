import json


cdef extern from "jv.h":
    ctypedef struct jv:
        pass
    int jv_is_valid(jv)
    char* jv_string_value(jv)
    jv jv_dump_string(jv, int flags)
    void jv_free(jv)


cdef extern from "jq.h":
    ctypedef struct jq_state:
        pass
        
    jq_state *jq_init()
    void jq_teardown(jq_state **)
    int jq_compile(jq_state *, const char* str)
    void jq_start(jq_state *, jv value, int flags)
    jv jq_next(jq_state *)
    
    
cdef extern from "jv_parse.h":
    cdef struct jv_parser:
        pass
    
    void jv_parser_init(jv_parser*)
    void jv_parser_free(jv_parser*)
    void jv_parser_set_buf(jv_parser*, const char*, int, int)
    jv jv_parser_next(jv_parser*)


def jq(char* program):
    cdef jq_state *jq = jq_init()
    if not jq:
        raise Exception("jq_init failed")
    
    # TODO: jq_compile prints error to stderr
    cdef int compiled = jq_compile(jq, program)
    
    if not compiled:
        raise ValueError("program was not valid")
    
    cdef _Program wrapped_program = _Program.__new__(_Program)
    wrapped_program._jq = jq
    return wrapped_program


cdef class _Program(object):
    cdef jq_state* _jq

    def __dealloc__(self):
        jq_teardown(&self._jq)
    
    def transform_string(self, char* input):
        result_strings = self._string_to_strings(input)
        return _Result(result_strings)
        
    def transform_json(self, object input):
        return self.transform_string(json.dumps(input))
        

    cdef object _string_to_strings(self, char* input):
        cdef jv_parser parser
        jv_parser_init(&parser)
        # TODO: is len a suitable replacement for strlen (unicode)?
        jv_parser_set_buf(&parser, input, len(input), 0)
        cdef jv value
        results = []
        while True:
            value = jv_parser_next(&parser)
            if jv_is_valid(value):
                self._process(value, results)
            else:
                break
                
        jv_parser_free(&parser)
        
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



class _Result(object):
    def __init__(self, strings):
        self._strings = strings
        
    def __str__(self):
        return "\n".join(self._strings)
        
    def json(self):
        return json.loads(str(self))
        
    def json_all(self):
        return map(json.loads, self._strings)
