from pathlib import Path
import jq
from .tools import assert_equal, assert_is

JQ_LIB_PATH = Path(__file__).parent / 'jq_lib'


def test_include_increment():
    exp = 'include "test_module"; . | increment'
    assert_equal(
        11,
        jq.compile(exp, library_search_path=[JQ_LIB_PATH]).input(10).first()
    )


def test_import_contant():
    exp = 'import "test_module" as test; . | test::constant_str'
    assert_equal(
        "constant",
        jq.compile(exp, library_search_path=[JQ_LIB_PATH]).input("test").first()
    )

