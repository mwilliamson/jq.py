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
    return _Program(program)


class _Program(object):
    def __init__(self, program):
        self._program = program
        
    def transform_string(self, input):
        return _Result(_string_to_strings(self._program, input))


class _Result(object):
    def __init__(self, strings):
        self._strings = strings
        
    def __str__(self):
        return "\n".join(self._strings)
        
    def json(self):
        return json.loads(str(self))
        
    def json_all(self):
        return map(json.loads, self._strings)


def _string_to_strings(char* program, char* input):
    cdef jq_state *jq
    # TODO: error if !jq
    jq = jq_init()
    # TODO: error if !compiled
    cdef int compiled = jq_compile(jq, program)
    
    cdef jv_parser parser
    jv_parser_init(&parser)
    # TODO: is len a suitable replacement for strlen (unicode)?
    jv_parser_set_buf(&parser, input, len(input), 0)
    cdef jv value
    results = []
    while True:
        value = jv_parser_next(&parser)
        if jv_is_valid(value):
            process(jq, value, results)
        else:
            break
            
    jv_parser_free(&parser)
    
    jq_teardown(&jq)
    return results


cdef process(jq_state *jq, jv value, output):
    cdef int jq_flags = 0
    
    jq_start(jq, value, jq_flags);
    cdef jv result
    cdef int dumpopts = 0
    cdef jv dumped
    
    while True:
        result = jq_next(jq)
        if not jv_is_valid(result):
            return output
        else:
            dumped = jv_dump_string(result, dumpopts)
            output.append(jv_string_value(dumped))
            jv_free(dumped)
