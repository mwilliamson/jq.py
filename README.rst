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

Call ``jq.compile`` to compile a jq program.
Call ``.input()`` on the compiled program to supply an input value.
The input must either be:

* a valid JSON value, such as the values returned from ``json.load``
* unparsed JSON text passed as the keyword argument ``text``.

Calling ``first()`` on the result will run the program with the given input,
and return the first output element.

.. code-block:: python

    import jq

    assert jq.compile(".").input("hello").first() == "hello"
    assert jq.compile(".").input(text='"hello"').first() == "hello"
    assert jq.compile("[.[]+1]").input([1, 2, 3]).first() == [2, 3, 4]
    assert jq.compile(".[]+1").input([1, 2, 3]).first() == 2

Call ``text()`` instead of ``first()`` to serialise the output into JSON text:

.. code-block:: python

    assert jq.compile(".").input("42").text() == '"42"'

When calling ``text()``, if there are multiple output elements, each element is represented by a separate line:

.. code-block:: python

    assert jq.compile(".[]").input([1, 2, 3]).text() == "1\n2\n3"

Call ``all()`` to get all of the output elements in a list:

.. code-block:: python

    assert jq.compile(".[]+1").input([1, 2, 3]).all() == [2, 3, 4]

Call ``iter()`` to get all of the output elements as an iterator:

.. code-block:: python

    iterator = iter(jq.compile(".[]+1").input([1, 2, 3]))
    assert next(iterator, None) == 2
    assert next(iterator, None) == 3
    assert next(iterator, None) == 4
    assert next(iterator, None) == None

Calling ``compile()`` with the ``args`` argument allows predefined variables to be used within the program:

.. code-block:: python

    program = jq.compile("$a + $b + .", args={"a": 100, "b": 20})
    assert program.input(3).first() == 123

Convenience functions are available to get the output for a program and input in one call:

.. code-block:: python

    assert jq.first(".[] + 1", [1, 2, 3]) == 2
    assert jq.first(".[] + 1", text="[1, 2, 3]") == 2
    assert jq.text(".[] + 1", [1, 2, 3]) == "2\n3\n4"
    assert jq.all(".[] + 1", [1, 2, 3]) == [2, 3, 4]
    assert list(jq.iter(".[] + 1", [1, 2, 3])) == [2, 3, 4]

The original program string is available on a compiled program as the ``program_string`` attribute:

.. code-block:: python

    program = jq.compile(".")
    assert program.program_string == "."
