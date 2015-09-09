jq.py: a lightweight and flexible JSON processor
================================================

This project contains Python bindings for
`jq <http://stedolan.github.io/jq/>`_.

Installation
------------

During installation,
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

A program can be compiled by passing it to ``jq.jq``.
To apply the program to an input, call the ``transform`` method.
jq.py expects the value to be valid JSON,
such as values returned from ``json.load``.

.. code-block:: python

    from jq import jq

    jq(".").transform("42") == "42"
    jq(".").transform({"a": 1}) == {"a": 1}

If the value is unparsed JSON text, pass it in using the ``text``
argument:

.. code-block:: python

    jq(".").transform(text="42") == 42

The ``text_output`` argument can be used to serialise the output into
JSON text:

.. code-block:: python

    jq(".").transform("42", text_output=True) == '"42"'

If there are multiple output elements, each element is represented by a
separate line, irrespective of the value of ``multiple_output``:

.. code-block:: python

    jq(".[]").transform([1, 2, 3], text_output=True) == "1\n2\n3"

If ``multiple_output`` is ``False`` (the default), then the first output
is used:

.. code-block:: python

    jq(".[]+1").transform([1, 2, 3]) == 2

If ``multiple_output`` is ``True``, all output elements are returned in
an array:

.. code-block:: python

    jq(".[]+1").transform([1, 2, 3], multiple_output=True) == [2, 3, 4]

