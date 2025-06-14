# coding=utf8

from __future__ import unicode_literals

import jq
from .tools import assert_equal, assert_is


def test_output_of_dot_operator_is_input():
    assert_equal(
        "42",
        jq.compile(".").input("42").first()
    )


def test_can_add_one_to_each_element_of_an_array():
    assert_equal(
        [2, 3, 4],
        jq.compile("[.[]+1]").input([1, 2, 3]).first()
    )


def test_nan_is_outputted_as_null():
    assert_equal(
        None,
        jq.compile("nan").input(0).first(),
    )


def test_positive_infinity_is_outputted_as_positive_max_double():
    assert_equal(
        1.7976931348623157e+308,
        jq.compile(". * 2").input(1.7976931348623157e+308).first(),
    )


def test_negative_infinity_is_outputted_as_negative_max_double():
    assert_equal(
        -1.7976931348623157e+308,
        jq.compile(". * 2").input(-1.7976931348623157e+308).first(),
    )


def test_can_use_regexes():
    assert_equal(
        True,
        jq.compile('test(".*")').input("42").first()
    )

    assert_equal(
        True,
        jq.compile('test("^[0-9]+$")').input("42").first()
    )

    assert_equal(
        False,
        jq.compile('test("^[0-9]+$")').input("42a").first()
    )


def test_when_text_argument_is_used_then_input_is_treated_as_json_text():
    assert_equal(
        42,
        jq.compile(".").input(text="42").first()
    )


def test_input_can_be_value():
    program = jq.compile(".")

    result = program.input_value("42").first()

    assert_equal("42", result)


def test_input_can_be_multiple_values():
    program = jq.compile(".")

    result = program.input_values([1, 2, 3]).all()

    assert_equal([1, 2, 3], result)


def test_input_can_be_text():
    program = jq.compile(".")

    result = program.input_text("42").first()

    assert_equal(42, result)


def test_input_can_be_text_with_multiple_values_separated_by_newlines():
    program = jq.compile(".")

    result = program.input_text("1\n2\n3").all()

    assert_equal([1, 2, 3], result)


def test_slurping_empty_input_text_reads_input_as_empty_array():
    program = jq.compile(".")

    result = program.input_text("1\n2\n3\n", slurp=True).all()

    assert_equal([[1, 2, 3]], result)


def test_slurping_input_text_reads_input_as_single_array():
    program = jq.compile(".")

    result = program.input_text("1\n2\n3\n", slurp=True).all()

    assert_equal([[1, 2, 3]], result)


def test_can_slurp_without_trailing_newline():
    program = jq.compile(".")

    result = program.input_text("1\n2\n3", slurp=True).all()

    assert_equal([[1, 2, 3]], result)


def test_can_slurp_and_produce_multiple_output_values():
    program = jq.compile(".[]")

    result = program.input_text("1\n2\n3", slurp=True).all()

    assert_equal([1, 2, 3], result)


def test_when_text_method_is_used_on_result_then_output_is_serialised_to_json_string():
    assert_equal(
        '"42"',
        jq.compile(".").input("42").text()
    )


def test_elements_in_text_output_are_separated_by_newlines():
    assert_equal(
        "1\n2\n3",
        jq.compile(".[]").input([1, 2, 3]).text()
    )


def test_when_first_method_is_used_on_result_then_first_element_of_result_is_returned():
    assert_equal(
        2,
        jq.compile(".[]+1").input([1, 2, 3]).first()
    )


def test_when_all_method_is_used_on_result_then_all_elements_are_returned_in_list():
    assert_equal(
        [2, 3, 4],
        jq.compile(".[]+1").input([1, 2, 3]).all()
    )


def test_can_treat_execute_result_as_iterable():
    iterator = iter(jq.compile(".[]+1").input([1, 2, 3]))
    assert_equal(2, next(iterator))
    assert_equal(3, next(iterator))
    assert_equal(4, next(iterator))
    assert_equal("end", next(iterator, "end"))


def test_can_execute_same_program_again_before_consuming_output_of_first_execution():
    program = jq.compile(".[]+1")
    first = iter(program.input([1, 2, 3]))
    assert_equal(2, next(first))
    second = iter(program.input([11, 12, 13]))
    assert_equal(12, next(second))
    assert_equal(3, next(first))
    assert_equal(4, next(first))
    assert_equal(13, next(second))
    assert_equal(14, next(second))


def test_iterators_from_same_program_and_input_are_independent():
    program_with_input = jq.compile(".[]+1").input([1, 2, 3])
    first = iter(program_with_input)
    assert_equal(2, next(first))
    second = iter(program_with_input)
    assert_equal(2, next(second))
    assert_equal(3, next(first))
    assert_equal(4, next(first))
    assert_equal(3, next(second))
    assert_equal(4, next(second))


def test_value_error_is_raised_if_program_is_invalid():
    try:
        jq.compile("!")
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
    program = jq.compile(".x")
    try:
        program.input(1).all()
        assert False, "Expected error"
    except ValueError as error:
        expected_error_str = "Cannot index number with string \"x\""
        assert_equal(str(error), expected_error_str)


def test_non_string_error_is_converted_to_json_text():
    program = jq.compile("error")
    try:
        program.input({"x": 1}).all()
        assert False, "Expected error"
    except ValueError as error:
        expected_error_str = '{"x": 1}'
        assert_equal(str(error), expected_error_str)


def test_errors_do_not_leak_between_transformations():
    program = jq.compile(".x")
    try:
        program.input(1).all()
        assert False, "Expected error"
    except ValueError as error:
        pass

    assert_equal(1, program.input({"x": 1}).first())


def test_value_error_is_raised_if_input_is_not_valid_json():
    program = jq.compile(".x")
    try:
        program.input(text="!!").first()
        assert False, "Expected error"
    except ValueError as error:
        expected_error_str = "parse error: Invalid numeric literal at EOF at line 1, column 2"
        assert_equal(str(error), expected_error_str)


def test_unicode_strings_can_be_used_as_input():
    assert_equal(
        "‽",
        jq.compile(".").input(text='"‽"').first()
    )


def test_unicode_strings_can_be_used_as_programs():
    assert_equal(
        "Dragon‽",
        jq.compile('.+"‽"').input(text='"Dragon"').first()
    )


def test_returned_integers_larger_than_32_bits_have_int_type():
    program = jq.compile("pow(.; 33)")

    result = program.input(2).first()

    assert_equal(2 ** 33, result)
    assert_equal(int, type(result))


def test_compiling_with_args_should_set_predefined_variables():
    assert_equal(
        123,
        jq.compile("$a + $b + .", args={"a": 100, "b": 20}).input(3).first()
    )


def test_repr_of_compile_result_is_compilation_string():
    program = jq.compile(".")
    repr_string = repr(program)
    assert_equal("jq.compile({!r})".format("."), repr_string)


def test_program_string_can_be_retrieved_from_program():
    program = jq.compile(".")
    assert_equal(".", program.program_string)


class TestJvToPython(object):
    def test_program_preserves_null(self):
        program = jq.compile(".")
        assert_is(None, program.input(text='null').first())

    def test_program_preserves_bools(self):
        program = jq.compile(".")
        assert_is(False, program.input(text="false").first())
        assert_is(True, program.input(text="true").first())

    def test_program_preserves_ints(self):
        program = jq.compile(".")
        assert_equal(int, type(program.input(text="0").first()))
        assert_equal(0, program.input(text="0").first())
        assert_equal(1, program.input(text="1").first())
        assert_equal(-1, program.input(text="-1").first())
        assert_equal(12345, program.input(text="12345").first())
        assert_equal(-12345, program.input(text="-12345").first())

    def test_program_preserves_floats(self):
        program = jq.compile(".")
        assert_equal(float, type(program.input(text="1.1").first()))
        assert_equal(3.14159, program.input(text="3.14159").first())
        assert_equal(-3.14159, program.input(text="-3.14159").first())
        assert_equal(42E100, program.input(text="42E100").first())
        assert_equal(-42E100, program.input(text="-42E100").first())

    def test_program_preserves_strings(self):
        program = jq.compile(".")
        assert_equal(type(""), type(program.input(text='""').first()))
        assert_equal("", program.input(text='""').first())
        assert_equal("x", program.input(text='"x"').first())
        assert_equal("xyz", program.input(text='"xyz"').first())

    def test_given_json_value_then_string_containing_null_characters_are_preserved(self):
        program = jq.compile(".")

        result = program.input("a\x00b").first()

        assert_equal("a\x00b", result)

    def test_given_json_text_then_strings_containing_null_characters_are_preserved(self):
        program = jq.compile(".")

        # Before jq 1.7.1, we expect jq to accept the literal null character.
        # From jq 1.7.1, we expect jq to reject the literal null character.

        try:
            result = program.input(text='"a\x00b"').first()

            assert_equal("a\x00b", result)
        except ValueError as error:
            assert_equal(
                "parse error: Invalid string: control characters from U+0000 " +
                "through U+001F must be escaped at line 1, column 5",
                str(error),
            )

    def test_program_preserves_arrays(self):
        program = jq.compile(".")

        assert_equal(list, type(program.input(text='[]').first()))

        assert_equal([], program.input(text='[]').first())

        assert_equal([1], program.input(text='[1]').first())
        assert_equal([1, 2], program.input(text='[1, 2]').first())

        assert_equal([3.14159], program.input(text='[3.14159]').first())
        assert_equal([3.14159, 95141.3], program.input(text='[3.14159, 95141.3]').first())

        assert_equal([False], program.input(text='[false]').first())
        assert_equal([False, True], program.input(text='[false, true]').first())

        assert_equal([[]], program.input(text='[[]]').first())
        assert_equal([[[]]], program.input(text='[[[]]]').first())
        assert_equal([[], []], program.input(text='[[], []]').first())
        assert_equal([[[], []], [[], []]], program.input(text='[[[], []], [[], []]]').first())

        assert_equal([{}], program.input(text='[{}]').first())
        assert_equal([{"": []}], program.input(text='[{"": []}]').first())
        assert_equal([{"1": [], "2": []}], program.input(text='[{"1": [], "2": []}]').first())

    def test_program_preserves_objects(self):
        program = jq.compile(".")

        assert_equal(dict, type(program.input(text='{}').first()))

        assert_equal({}, program.input(text='{}').first())

        assert_equal({"": True}, program.input(text='{"": true}').first())
        assert_equal({"": False}, program.input(text='{"": false}').first())

        assert_equal({"": 0}, program.input(text='{"": 0}').first())
        assert_equal({"": 1}, program.input(text='{"": 1}').first())
        assert_equal({"a": 0, "b": 1}, program.input(text='{"a": 0, "b": 1}').first())
        assert_equal({"": 3.14159}, program.input(text='{"": 3.14159}').first())
        assert_equal({"a": 3.14159, "b": 95141.3},
                     program.input(text='{"a": 3.14159, "b": 95141.3}').first())

        assert_equal({"": ""}, program.input(text='{"": ""}').first())
        assert_equal({"": "x"}, program.input(text='{"": "x"}').first())

        assert_equal({"": []}, program.input(text='{"": []}').first())
        assert_equal({"": [{}]}, program.input(text='{"": [{}]}').first())
        assert_equal({"a": [1], "b": [2]},
                     program.input(text='{"a": [1], "b": [2]}').first())

        assert_equal({"": {}}, program.input(text='{"": {}}').first())
        assert_equal({"a": {}, "b": {}}, program.input(text='{"a": {}, "b": {}}').first())
        assert_equal({"": {"": {}}}, program.input(text='{"": {"": {}}}').first())

    def test_object_keys_containing_null_characters_are_preserved(self):
        program = jq.compile(".")

        result = program.input({"a\x00b": None}).first()

        assert_equal({"a\x00b": None}, result)


class TestConvenienceFunctions(object):
    def test_first_function_with_json_value_input_returns_first_output_element(self):
        output = jq.first(".[] + 1", [1, 2, 3])

        assert_equal(2, output)

    def test_first_function_with_json_text_input_returns_first_output_element(self):
        output = jq.first(".[] + 1", text="[1, 2, 3]")

        assert_equal(2, output)

    def test_text_function_with_json_value_input_returns_all_output_elements_as_string(self):
        output = jq.text(".[] + 1", [1, 2, 3])

        assert_equal("2\n3\n4", output)

    def test_text_function_with_json_text_input_returns_all_output_elements_as_string(self):
        output = jq.text(".[] + 1", text="[1, 2, 3]")

        assert_equal("2\n3\n4", output)

    def test_all_function_with_json_value_input_returns_all_output_elements_in_list(self):
        output = jq.all(".[] + 1", [1, 2, 3])

        assert_equal([2, 3, 4], output)

    def test_all_function_with_json_text_input_returns_all_output_element_in_list(self):
        output = jq.all(".[] + 1", text="[1, 2, 3]")

        assert_equal([2, 3, 4], output)

    def test_iter_function_with_json_value_input_returns_all_output_elements_in_iterator(self):
        iterator = jq.iter(".[] + 1", [1, 2, 3])

        assert_equal(2, next(iterator))
        assert_equal(3, next(iterator))
        assert_equal(4, next(iterator))
        assert_equal("end", next(iterator, "end"))

    def test_iter_function_with_json_text_input_returns_all_output_element_in_iterator(self):
        iterator = jq.iter(".[] + 1", text="[1, 2, 3]")

        assert_equal(2, next(iterator))
        assert_equal(3, next(iterator))
        assert_equal(4, next(iterator))
        assert_equal("end", next(iterator, "end"))
