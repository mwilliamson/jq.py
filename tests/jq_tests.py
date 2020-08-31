# coding=utf8

from __future__ import unicode_literals

from nose.tools import istest, assert_equal, assert_raises

import jq


@istest
def output_of_dot_operator_is_input():
    assert_equal(
        "42",
        jq.compile(".").input("42").first()
    )


@istest
def can_add_one_to_each_element_of_an_array():
    assert_equal(
        [2, 3, 4],
        jq.compile("[.[]+1]").input([1, 2, 3]).first()
    )


@istest
def can_use_regexes():
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


@istest
def when_text_argument_is_used_then_input_is_treated_as_json_text():
    assert_equal(
        42,
        jq.compile(".").input(text="42").first()
    )


@istest
def when_text_method_is_used_on_result_then_output_is_serialised_to_json_string():
    assert_equal(
        '"42"',
        jq.compile(".").input("42").text()
    )


@istest
def elements_in_text_output_are_separated_by_newlines():
    assert_equal(
        "1\n2\n3",
        jq.compile(".[]").input([1, 2, 3]).text()
    )


@istest
def when_first_method_is_used_on_result_then_first_element_of_result_is_returned():
    assert_equal(
        2,
        jq.compile(".[]+1").input([1, 2, 3]).first()
    )


@istest
def when_all_method_is_used_on_result_then_all_elements_are_returned_in_list():
    assert_equal(
        [2, 3, 4],
        jq.compile(".[]+1").input([1, 2, 3]).all()
    )


@istest
def can_treat_execute_result_as_iterable():
    iterator = iter(jq.compile(".[]+1").input([1, 2, 3]))
    assert_equal(2, next(iterator))
    assert_equal(3, next(iterator))
    assert_equal(4, next(iterator))
    assert_equal("end", next(iterator, "end"))


@istest
def can_execute_same_program_again_before_consuming_output_of_first_execution():
    program = jq.compile(".[]+1")
    first = iter(program.input([1, 2, 3]))
    assert_equal(2, next(first))
    second = iter(program.input([11, 12, 13]))
    assert_equal(12, next(second))
    assert_equal(3, next(first))
    assert_equal(4, next(first))
    assert_equal(13, next(second))
    assert_equal(14, next(second))


@istest
def iterators_from_same_program_and_input_are_independent():
    program_with_input = jq.compile(".[]+1").input([1, 2, 3])
    first = iter(program_with_input)
    assert_equal(2, next(first))
    second = iter(program_with_input)
    assert_equal(2, next(second))
    assert_equal(3, next(first))
    assert_equal(4, next(first))
    assert_equal(3, next(second))
    assert_equal(4, next(second))


@istest
def multiple_inputs_in_text_input_are_separated_by_newlines():
    assert_equal(
        [2, 3, 4],
        jq.compile(".+1").input(text="1\n2\n3").all()
    )


@istest
def value_error_is_raised_if_program_is_invalid():
    try:
        jq.compile("!")
        assert False, "Expected error"
    except ValueError as error:
        expected_error_str = "jq: error: syntax error, unexpected INVALID_CHARACTER, expecting $end (Unix shell quoting issues?) at <top-level>, line 1:\n!\njq: 1 compile error"
        assert_equal(str(error), expected_error_str)


@istest
def value_error_is_raised_if_input_cannot_be_processed_by_program():
    program = jq.compile(".x")
    try:
        program.input(1).all()
        assert False, "Expected error"
    except ValueError as error:
        expected_error_str = "Cannot index number with string \"x\""
        assert_equal(str(error), expected_error_str)


@istest
def errors_do_not_leak_between_transformations():
    program = jq.compile(".x")
    try:
        program.input(1).all()
        assert False, "Expected error"
    except ValueError as error:
        pass

    assert_equal(1, program.input({"x": 1}).first())


@istest
def value_error_is_raised_if_input_is_not_valid_json():
    program = jq.compile(".x")
    try:
        program.input(text="!!").first()
        assert False, "Expected error"
    except ValueError as error:
        expected_error_str = "parse error: Invalid numeric literal at EOF at line 1, column 2"
        assert_equal(str(error), expected_error_str)


@istest
def unicode_strings_can_be_used_as_input():
    assert_equal(
        "‽",
        jq.compile(".").input(text='"‽"').first()
    )


@istest
def unicode_strings_can_be_used_as_programs():
    assert_equal(
        "Dragon‽",
        jq.compile('.+"‽"').input(text='"Dragon"').first()
    )


@istest
def repr_of_compile_result_is_compilation_string():
    program = jq.compile(".")
    repr_string = repr(program)
    assert_equal("jq.compile({!r})".format("."), repr_string)


@istest
def program_string_can_be_retrieved_from_program():
    program = jq.compile(".")
    assert_equal(".", program.program_string)

@istest
def empty_text_iterator_stops():
    program = jq.compile(".")
    assert_raises(StopIteration, program.input(text=iter([])).first)
    assert_raises(StopIteration, program.input(text=iter([""])).first)
    assert_raises(StopIteration, program.input(text=iter(["", ""])).first)

@istest
def empty_value_iterator_stops():
    program = jq.compile(".")
    assert_raises(StopIteration, program.input(value=iter([])).first)

@istest
def single_value_iterator_works():
    program = jq.compile(".")
    assert_equal(False, program.input(value=iter([False])).first())
    assert_equal(True, program.input(value=iter([True])).first())
    assert_equal(42, program.input(value=iter([42])).first())
    assert_equal(-42, program.input(value=iter([-42])).first())
    assert_equal("42", program.input(value=iter(["42"])).first())
    assert_equal([42], program.input(value=iter([[42]])).first())
    assert_equal(dict(a=42), program.input(value=iter([dict(a=42)])).first())

@istest
def double_value_iterator_works():
    program = jq.compile(".")
    assert_equal([False, True],
                 program.input(value=iter([False, True])).all())
    assert_equal([True, False],
                 program.input(value=iter([True, False])).all())
    assert_equal([42, 24],
                 program.input(value=iter([42, 24])).all())
    assert_equal([-42, -24],
                 program.input(value=iter([-42, -24])).all())
    assert_equal(["42", "24"],
                 program.input(value=iter(["42", "24"])).all())
    assert_equal([[42], [24]],
                 program.input(value=iter([[42], [24]])).all())
    assert_equal([dict(a=42), dict(a=24)],
                 program.input(value=iter([dict(a=42), dict(a=24)])).all())

@istest
def single_complete_text_iterator_works():
    program = jq.compile(".")
    assert_equal(False, program.input(text=iter(["false"])).first())
    assert_equal(True, program.input(text=iter(["true"])).first())
    assert_equal(42, program.input(text=iter(["42"])).first())
    assert_equal(-42, program.input(text=iter(["-42"])).first())
    assert_equal("42", program.input(text=iter(['"42"'])).first())
    assert_equal([42], program.input(text=iter(["[42]"])).first())
    assert_equal(dict(a=42), program.input(text=iter(['{"a": 42}'])).first())

@istest
def multi_complete_text_iterator_works():
    program = jq.compile(".")
    assert_equal(False, program.input(text=iter(["fa", "lse"])).first())
    assert_equal(True, program.input(text=iter(["tr", "ue"])).first())
    assert_equal(42, program.input(text=iter(["4", "2"])).first())
    assert_equal(-42, program.input(text=iter(["-4", "2"])).first())
    assert_equal("42", program.input(text=iter(['"4', '2"'])).first())
    assert_equal([42], program.input(text=iter(["[4", "2]"])).first())
    assert_equal(dict(a=42), program.input(text=iter(['{"a":', ' 42}'])).first())

@istest
def single_incomplete_text_iterator_breaks():
    program = jq.compile(".")
    assert_raises(ValueError, program.input(text=iter(["fals"])).first)
    assert_raises(ValueError, program.input(text=iter(["tru"])).first)
    assert_raises(ValueError, program.input(text=iter(["-"])).first)
    assert_raises(ValueError, program.input(text=iter(['"42'])).first)
    assert_raises(ValueError, program.input(text=iter(["[42"])).first)
    assert_raises(ValueError, program.input(text=iter(['{"a": 42'])).first)

@istest
def multi_incomplete_text_iterator_breaks():
    program = jq.compile(".")
    assert_raises(ValueError, program.input(text=iter(["fa", "ls"])).first)
    assert_raises(ValueError, program.input(text=iter(["tr", "u"])).first)
    assert_raises(ValueError, program.input(text=iter(['"4', '2'])).first)
    assert_raises(ValueError, program.input(text=iter(["[4", "2"])).first)
    assert_raises(ValueError, program.input(text=iter(['{"a":', ' 42'])).first)

@istest
class ConvenienceFunctions(object):
    @istest
    def first_function_with_json_value_input_returns_first_output_element(self):
        output = jq.first(".[] + 1", [1, 2, 3])

        assert_equal(2, output)

    @istest
    def first_function_with_json_text_input_returns_first_output_element(self):
        output = jq.first(".[] + 1", text="[1, 2, 3]")

        assert_equal(2, output)

    @istest
    def text_function_with_json_value_input_returns_all_output_elements_as_string(self):
        output = jq.text(".[] + 1", [1, 2, 3])

        assert_equal("2\n3\n4", output)

    @istest
    def text_function_with_json_text_input_returns_all_output_elements_as_string(self):
        output = jq.text(".[] + 1", text="[1, 2, 3]")

        assert_equal("2\n3\n4", output)

    @istest
    def all_function_with_json_value_input_returns_all_output_elements_in_list(self):
        output = jq.all(".[] + 1", [1, 2, 3])

        assert_equal([2, 3, 4], output)

    @istest
    def all_function_with_json_text_input_returns_all_output_element_in_list(self):
        output = jq.all(".[] + 1", text="[1, 2, 3]")

        assert_equal([2, 3, 4], output)

    @istest
    def iter_function_with_json_value_input_returns_all_output_elements_in_iterator(self):
        iterator = jq.iter(".[] + 1", [1, 2, 3])

        assert_equal(2, next(iterator))
        assert_equal(3, next(iterator))
        assert_equal(4, next(iterator))
        assert_equal("end", next(iterator, "end"))

    @istest
    def iter_function_with_json_text_input_returns_all_output_element_in_iterator(self):
        iterator = jq.iter(".[] + 1", text="[1, 2, 3]")

        assert_equal(2, next(iterator))
        assert_equal(3, next(iterator))
        assert_equal(4, next(iterator))
        assert_equal("end", next(iterator, "end"))
