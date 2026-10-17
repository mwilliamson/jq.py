# coding=utf8
"""Tests for thread-safety of jq compilation and execution.

These tests verify correctness under concurrent access: no deadlocks,
no data corruption, and correct results when multiple threads use jq.

GIL release during compilation is verified by code review (pointer lifetimes,
error callback GIL reacquisition). Timing-based parallelism verification is
inherently non-deterministic and not suitable for CI.
"""

import threading

import jq


def test_compilation_with_errors_still_works():
    """Verify error handling works correctly with GIL release.

    The error callback needs to reacquire the GIL to manipulate Python
    objects. This test ensures that still works correctly.
    """
    try:
        jq.compile("this is not valid jq syntax !")
        assert False, "Expected ValueError for invalid syntax"
    except ValueError as e:
        # Error message should be present
        assert str(e), "Error message should not be empty"


def test_concurrent_compilations():
    """Verify multiple threads can compile concurrently without deadlock.

    Tests both jq_compile and jq_compile_args code paths under concurrent load.
    Uses a barrier to ensure all threads start simultaneously, maximizing
    concurrent execution. Note: jq.py uses a compilation lock, so compilations
    serialize within jq itself, but this test verifies no deadlocks occur.
    """
    results = {}
    errors = []
    barrier = threading.Barrier(5)  # 4 workers + 1 main thread

    def compile_expr(name: str, expr: str, args=None):
        barrier.wait()  # Wait for all threads to be ready
        try:
            program = jq.compile(expr, args=args)
            results[name] = program.input({"x": 1}).first()
        except Exception as e:
            errors.append((name, e))

    threads = [
        threading.Thread(target=compile_expr, args=("a", ".x")),
        threading.Thread(target=compile_expr, args=("b", ".x + 1")),
        threading.Thread(target=compile_expr, args=("c", ".x * 2")),
        # Include one with args to exercise jq_compile_args path
        threading.Thread(target=compile_expr, args=("d", ".x + $offset"), kwargs={"args": {"offset": 10}}),
    ]

    for t in threads:
        t.start()
    barrier.wait()  # Release all workers simultaneously
    for t in threads:
        t.join(timeout=5.0)

    assert not errors, f"Compilation errors: {errors}"
    assert results == {"a": 1, "b": 2, "c": 2, "d": 11}


def test_concurrent_execution_same_program():
    """Verify multiple threads can safely execute the same compiled program.

    This tests _JqStatePool acquire/release under contention. The pool
    holds a single jq_state, so concurrent access must serialize correctly.
    Uses a barrier to ensure all threads start simultaneously.
    """
    program = jq.compile(".x * 2")
    results = []
    errors = []
    num_threads = 10
    iterations_per_thread = 20
    barrier = threading.Barrier(num_threads + 1)  # workers + main thread

    def run_program(thread_id: int):
        barrier.wait()  # Wait for all threads to be ready
        try:
            for i in range(iterations_per_thread):
                value = thread_id * 100 + i
                result = program.input({"x": value}).first()
                results.append((value, result))
        except Exception as e:
            errors.append((thread_id, e))

    threads = [
        threading.Thread(target=run_program, args=(tid,))
        for tid in range(num_threads)
    ]

    for t in threads:
        t.start()
    barrier.wait()  # Release all workers simultaneously
    for t in threads:
        t.join(timeout=10.0)

    assert not errors, f"Execution errors: {errors}"
    assert len(results) == num_threads * iterations_per_thread

    for value, result in results:
        assert result == value * 2, f"Expected {value * 2}, got {result}"


def test_concurrent_compilation_errors():
    """Verify error callback handles concurrent compilation failures safely.

    Multiple threads compiling invalid expressions will all invoke the
    _store_error callback, which must safely reacquire the GIL via 'with gil'.
    Uses a barrier to ensure all threads start simultaneously.
    """
    errors_caught = []
    unexpected_errors = []
    num_threads = 10
    barrier = threading.Barrier(num_threads + 1)  # workers + main thread

    def compile_invalid(thread_id: int):
        barrier.wait()  # Wait for all threads to be ready
        try:
            # Each thread compiles a different invalid expression
            jq.compile(f"this is invalid syntax {thread_id} !")
            unexpected_errors.append((thread_id, "No exception raised"))
        except ValueError as e:
            errors_caught.append((thread_id, str(e)))
        except Exception as e:
            unexpected_errors.append((thread_id, e))

    threads = [
        threading.Thread(target=compile_invalid, args=(tid,))
        for tid in range(num_threads)
    ]

    for t in threads:
        t.start()
    barrier.wait()  # Release all workers simultaneously
    for t in threads:
        t.join(timeout=10.0)

    assert not unexpected_errors, f"Unexpected errors: {unexpected_errors}"
    assert len(errors_caught) == num_threads, (
        f"Expected {num_threads} ValueErrors, got {len(errors_caught)}"
    )
    for thread_id, error_msg in errors_caught:
        assert error_msg, f"Thread {thread_id} got empty error message"
