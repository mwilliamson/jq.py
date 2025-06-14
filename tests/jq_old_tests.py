# coding=utf8

from __future__ import unicode_literals

from jq import jq
from .tools import assert_equal


def test_output_of_dot_operator_is_input():
    assert_equal(
        "42",
        jq(".").transform("42")
    )


def test_can_add_one_to_each_element_of_an_array():
    assert_equal(
        [2, 3, 4],
        jq("[.[]+1]").transform([1, 2, 3])
    )


def test_can_use_regexes():
    assert_equal(
        True,
        jq('test(".*")').transform("42")
    )


def test_input_string_is_parsed_to_json_if_raw_input_is_true():
    assert_equal(
        42,
        jq(".").transform(text="42")
    )


def test_output_is_serialised_to_json_string_if_text_output_is_true():
    assert_equal(
        '"42"',
        jq(".").transform("42", text_output=True)
    )


def test_elements_in_text_output_are_separated_by_newlines():
    assert_equal(
        "1\n2\n3",
        jq(".[]").transform([1, 2, 3], text_output=True)
    )


def test_first_output_element_is_returned_if_multiple_output_is_false_but_there_are_multiple_output_elements():
    assert_equal(
        2,
        jq(".[]+1").transform([1, 2, 3])
    )


def test_multiple_output_elements_are_returned_if_multiple_output_is_true():
    assert_equal(
        [2, 3, 4],
        jq(".[]+1").transform([1, 2, 3], multiple_output=True)
    )


def test_multiple_inputs_in_raw_input_are_separated_by_newlines():
    assert_equal(
        [2, 3, 4],
        jq(".+1").transform(text="1\n2\n3", multiple_output=True)
    )


def test_value_error_is_raised_if_program_is_invalid():
    try:
        jq("!")
        assert False, "Expected error"
    except ValueError as error:
        expected_error_strs = [
            # jq 1.6 on Unix
            "jq: error: syntax error, unexpected INVALID_CHARACTER, expecting $end (Unix shell quoting issues?) at <top-level>, line 1:\n!\njq: 1 compile error",
            # jq 1.6 on Windows
            "jq: error: syntax error, unexpected INVALID_CHARACTER, expecting $end (Windows cmd shell quoting issues?) at <top-level>, line 1:\n!\njq: 1 compile error",
            # jq 1.7 on Unix
            "jq: error: syntax error, unexpected INVALID_CHARACTER, expecting end of file (Unix shell quoting issues?) at <top-level>, line 1:\n!\njq: 1 compile error",
            # jq 1.7 on Windows
            "jq: error: syntax error, unexpected INVALID_CHARACTER, expecting end of file (Windows cmd shell quoting issues?) at <top-level>, line 1:\n!\njq: 1 compile error",
            # jq 1.8
            "jq: error: syntax error, unexpected INVALID_CHARACTER, expecting end of file at <top-level>, line 1, column 1:\n    !\n    ^\njq: 1 compile error",
        ]
        assert str(error) in expected_error_strs


def test_value_error_is_raised_if_input_cannot_be_processed_by_program():
    program = jq(".x")
    try:
        program.transform(1)
        assert False, "Expected error"
    except ValueError as error:
        expected_error_str = "Cannot index number with string \"x\""
        assert_equal(str(error), expected_error_str)


def test_errors_do_not_leak_between_transformations():
    program = jq(".x")
    try:
        program.transform(1)
        assert False, "Expected error"
    except ValueError as error:
        pass

    assert_equal(1, program.transform({"x": 1}))


def test_value_error_is_raised_if_input_is_not_valid_json():
    program = jq(".x")
    try:
        program.transform(text="!!")
        assert False, "Expected error"
    except ValueError as error:
        expected_error_str = "parse error: Invalid numeric literal at EOF at line 1, column 2"
        assert_equal(str(error), expected_error_str)


def test_unicode_strings_can_be_used_as_input():
    assert_equal(
        "‽",
        jq(".").transform(text='"‽"')
    )


def test_unicode_strings_can_be_used_as_programs():
    assert_equal(
        "Dragon‽",
        jq('.+"‽"').transform(text='"Dragon"')
    )
