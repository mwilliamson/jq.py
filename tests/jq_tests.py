from nose.tools import istest, assert_equal

import jq


@istest
def dot_operator_does_nothing():
    assert_equal(
        "42",
        jq.string_to_string(".", "42")
    )


@istest
def can_add_one_to_each_element_of_an_array():
    assert_equal(
        "[2,3,4]",
        jq.string_to_string("[.[]+1]", "[1,2,3]")
    )


@istest
def output_elements_are_separated_by_newlines():
    assert_equal(
        "1\n2\n3",
        jq.string_to_string(".[]", "[1,2,3]")
    )


@istest
def string_to_json_parses_json_output():
    assert_equal(
        [1, 2, 3],
        jq.string_to_json("[.[]]", "[1,2,3]")
    )
