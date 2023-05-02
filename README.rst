jq.py: a lightweight and flexible JSON processor
================================================

This project contains Python bindings for
`jq <http://stedolan.github.io/jq/>`_.

Installation
------------

Wheels are built for various Python versions and architectures on Linux and Mac OS X.
On these platforms, you should be able to install jq with a normal pip install:

.. code-block:: sh

    pip install jq

If a wheel is not available,
the source for jq 1.6 is downloaded over HTTPS and built.
This requires:

* Autoreconf

* The normal C compiler toolchain, such as gcc and make.

* libtool

* Python headers.

Debian, Ubuntu or relatives
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If on Debian, Ubuntu or relatives, running the following command should be sufficient:

.. code-block:: sh

    apt-get install autoconf automake build-essential libtool python-dev

Red Hat, Fedora, CentOS or relatives
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If on Red Hat, Fedora, CentOS, or relatives, running the following command should be sufficient:

.. code-block:: sh

    yum groupinstall "Development Tools"
    yum install autoconf automake libtool python python-devel

Mac OS X
~~~~~~~~

If on Mac OS X, you probably want to install
`Xcode <https://developer.apple.com/xcode/>`_ and `Homebrew <http://brew.sh/>`_.
Once Homebrew is installed, you can install the remaining dependencies with:

.. code-block:: sh

    brew install autoconf automake libtool

Usage
-----

Using jq requires three steps:

#. Call ``jq.compile()`` to compile a jq program.
#. Call an input method on the compiled program to supply the input.
#. Call an output method on the result to retrieve the output.

For instance:

.. code-block:: python

    import jq

    assert jq.compile(".+5").input_value(42).first() == 47

Input methods
~~~~~~~~~~~~~

Call ``.input_value()`` to supply a valid JSON value, such as the values returned from ``json.load``:

.. code-block:: python

    import jq

    assert jq.compile(".").input_value(None).first() == None
    assert jq.compile(".").input_value(42).first() == 42
    assert jq.compile(".").input_value(0.42).first() == 0.42
    assert jq.compile(".").input_value(True).first() == True
    assert jq.compile(".").input_value("hello").first() == "hello"

Call ``.input_values()`` to supply multiple valid JSON values, such as the values returned from ``json.load``:

.. code-block:: python

    import jq

    assert jq.compile(".+5").input_values([1, 2, 3]).all() == [6, 7, 8]

Call ``.input_text()`` to supply unparsed JSON text:

.. code-block:: python

    import jq

    assert jq.compile(".").input_text("null").first() == None
    assert jq.compile(".").input_text("42").first() == 42
    assert jq.compile(".").input_text("0.42").first() == 0.42
    assert jq.compile(".").input_text("true").first() == True
    assert jq.compile(".").input_text('"hello"').first() == "hello"
    assert jq.compile(".").input_text("1\n2\n3").all() == [1, 2, 3]

Pass ``slurp=True`` to ``.input_text()`` to read the entire input into an array:

.. code-block:: python

    import jq

    assert jq.compile(".").input_text("1\n2\n3", slurp=True).first() == [1, 2, 3]

You can also call the older ``input()`` method by passing:

* a valid JSON value, such as the values returned from ``json.load``, as a positional argument
* unparsed JSON text as the keyword argument ``text``

For instance:

.. code-block:: python

    import jq

    assert jq.compile(".").input("hello").first() == "hello"
    assert jq.compile(".").input(text='"hello"').first() == "hello"

Return methods
~~~~~~~~~~~~~~

Calling ``first()`` on the result will run the program with the given input,
and return the first output element.

.. code-block:: python

    import jq

    assert jq.compile(".").input_value("hello").first() == "hello"
    assert jq.compile("[.[]+1]").input_value([1, 2, 3]).first() == [2, 3, 4]
    assert jq.compile(".[]+1").input_value([1, 2, 3]).first() == 2

Call ``text()`` instead of ``first()`` to serialise the output into JSON text:

.. code-block:: python

    assert jq.compile(".").input_value("42").text() == '"42"'

When calling ``text()``, if there are multiple output elements, each element is represented by a separate line:

.. code-block:: python

    assert jq.compile(".[]").input_value([1, 2, 3]).text() == "1\n2\n3"

Call ``all()`` to get all of the output elements in a list:

.. code-block:: python

    assert jq.compile(".[]+1").input_value([1, 2, 3]).all() == [2, 3, 4]

Call ``iter()`` to get all of the output elements as an iterator:

.. code-block:: python

    iterator = iter(jq.compile(".[]+1").input_value([1, 2, 3]))
    assert next(iterator, None) == 2
    assert next(iterator, None) == 3
    assert next(iterator, None) == 4
    assert next(iterator, None) == None

Arguments
~~~~~~~~~

Calling ``compile()`` with the ``args`` argument allows predefined variables to be used within the program:

.. code-block:: python

    program = jq.compile("$a + $b + .", args={"a": 100, "b": 20})
    assert program.input_value(3).first() == 123

Convenience functions
~~~~~~~~~~~~~~~~~~~~~

Convenience functions are available to get the output for a program and input in one call:

.. code-block:: python

    assert jq.first(".[] + 1", [1, 2, 3]) == 2
    assert jq.first(".[] + 1", text="[1, 2, 3]") == 2
    assert jq.text(".[] + 1", [1, 2, 3]) == "2\n3\n4"
    assert jq.all(".[] + 1", [1, 2, 3]) == [2, 3, 4]
    assert list(jq.iter(".[] + 1", [1, 2, 3])) == [2, 3, 4]

Original program string
~~~~~~~~~~~~~~~~~~~~~~~

The original program string is available on a compiled program as the ``program_string`` attribute:

.. code-block:: python

    program = jq.compile(".")
    assert program.program_string == "."
