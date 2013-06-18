cdef extern from "jv.h":
    ctypedef struct jv:
        pass
    int jv_is_valid(jv)
    char* jv_string_value(jv)
    jv jv_dump_string(jv, int flags)


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
    


def string_to_string(char* program, char* input):
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
            results.append(process(jq, value))
        else:
            break
            
    jv_parser_free(&parser)
    
    jq_teardown(&jq)
    return "".join(results)


cdef process(jq_state *jq, jv value):
    cdef int jq_flags = 0
    
    jq_start(jq, value, jq_flags);
    cdef jv result
    cdef int dumpopts = 0
    cdef jv dumped
    
    output = []
    
    while True:
        result = jq_next(jq)
        if not jv_is_valid(result):
            return "\n".join(output)
        else:
            dumped = jv_dump_string(result, dumpopts)
            output.append(jv_string_value(dumped))
            # TODO: free dumped
