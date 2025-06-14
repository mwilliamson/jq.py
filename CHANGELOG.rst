Changelog
=========

1.9.0
-----

* Update to jq 1.8.0.

* Drop support for Python 3.6

* Distribute Cython sources instead of C sources to improve compatibility.

1.8.0
-----

* Drop support for Python 3.5.

* Add support for Python 3.13.

* Build Windows wheels.

1.7.0
-----

* Update to jq 1.7.1.

* Include tox.ini in sdist.

* Use the version of oniguruma distributed with jq.

1.6.0
-----

* Update to jq 1.7.

* Add support for building with Cython 3.

* Add support for building with the system libjq and libonig instead of building
  using the bundled source.

* Include tests in sdist.

1.5.0
-----

* Add input_value, input_values and input_text methods as replacements for the
  input method. The input method is still supported.

* Add support for slurp when calling input_text.

* Add support for Python 3.12.

* Build macOS arm64 wheels.

1.4.1
-----

* Improve handling of null bytes in program inputs and outputs.

1.4.0
-----

* Update handling of non-finite numbers to match the behaviour jq 1.6.
  Specifically, NaN is outputted as None, Inf is outputted as DBL_MAX,
  and -Inf is outputted as DBL_MIN.

1.3.0
-----

* The jq and oniguruma libraries that these Python bindings rely on are now
  included in the source distribution, instead of being downloaded.

1.2.3
-----

* Add support for Python 3.11.

1.2.2
-----

* Include support for more wheels, including aarch64 on Linux.

1.2.1
-----

* Drop support for Python 2.7 and Python 3.4.

1.2.0 (Unreleased)
------------------

* Return integers larger than 32 bits as ints.

1.1.3
-----

* Include LICENSE in sdist.

1.1.2
-----

* Handle MACOSX_DEPLOYMENT_TARGET being an integer to improve macOS Big Sur support.

1.1.1
-----

* Update cibuildwheel to 1.6.2 to fix building of OS X wheels.

1.1.0
-----

* Add support for predefined variables.
