# coding=utf8

from nose.tools import istest, assert_equal, assert_raises

from jq import jq


@istest
def output_of_dot_operator_is_input():
    assert_equal(
        "42",
        jq(".").transform("42")
    )


@istest
def can_add_one_to_each_element_of_an_array():
    assert_equal(
        [2, 3, 4],
        jq("[.[]+1]").transform([1, 2, 3])
    )


@istest
def input_string_is_parsed_to_json_if_raw_input_is_true():
    assert_equal(
        42,
        jq(".").transform("42", raw_input=True)
    )


@istest
def output_is_serialised_to_json_string_if_raw_output_is_true():
    assert_equal(
        '"42"',
        jq(".").transform("42", raw_output=True)
    )


@istest
def elements_in_raw_output_are_separated_by_newlines():
    assert_equal(
        "1\n2\n3",
        jq(".[]").transform([1, 2, 3], raw_output=True)
    )


@istest
def first_output_element_is_returned_if_multiple_output_is_false_but_there_are_multiple_output_elements():
    assert_equal(
        2,
        jq(".[]+1").transform([1, 2, 3])
    )


@istest
def multiple_output_elements_are_returned_if_multiple_output_is_true():
    assert_equal(
        [2, 3, 4],
        jq(".[]+1").transform([1, 2, 3], multiple_output=True)
    )


@istest
def multiple_inputs_in_raw_input_are_separated_by_newlines():
    assert_equal(
        [2, 3, 4],
        jq(".+1").transform("1\n2\n3", raw_input=True, multiple_output=True)
    )


@istest
def value_error_is_raised_if_program_is_invalid():
    assert_raises(ValueError, lambda: jq("!"))


@istest
def unicode_strings_can_be_used_as_input():
    assert_equal(
        u"‽",
        jq(".").transform(u'"‽"', raw_input=True)
    )


@istest
def unicode_strings_can_be_used_as_programs():
    assert_equal(
        u"Dragon‽",
        jq(u'.+"‽"').transform(u'"Dragon"', raw_input=True)
    )
