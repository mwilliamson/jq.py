jq.py: a lightweight and flexible JSON processor
================================================

This project contains Python bindings for
`jq <http://stedolan.github.io/jq/>`_.

Installation
------------

**These docs are for the development version of jq.
Feedback on the new API would be much appreciated!**

Wheels are built for various Python versions and architectures on Linux and Mac OS X.
On these platforms, you should be able to install jq with a normal pip install:

.. code-block:: sh

    pip install jq --pre

If a wheel is not available,
the source for jq 1.5 is downloaded over HTTPS and built.
Therefore, installation requires any programs required to build jq.
This includes:

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
    yum install autoconf automake libtool python

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
