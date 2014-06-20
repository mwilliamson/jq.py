jq.py: a lightweight and flexible JSON processor
================================================

This project contains Python bindings for
`jq <http://stedolan.github.io/jq/>`_.

Installation
------------

During installation,
jq 1.4 is downloaded over HTTPS from GitHub and built.
Therefore, installation requires any programs required to build jq.
This includes:

* The normal C compiler toolchain, such as gcc and make.
  Installable on Debian, Ubuntu and relatives by installing the package ``build-essential``.

* Autoconf

* Flex

* Bison

Usage
-----

A program can be compiled by passing it to ``jq.jq``.
To apply the program to an input, called the ``transform`` method.
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

    jq(".[]").transform("[1, 2, 3]", text_output=True) == "1\n2\n3"

If ``multiple_output`` is ``False`` (the default), then the first output
is used:

.. code-block:: python

    jq(".[]+1").transform([1, 2, 3]) == 2

If ``multiple_output`` is ``True``, all output elements are returned in
an array:

.. code-block:: python

    jq(".[]+1").transform([1, 2, 3], multiple_output=True) == [2, 3, 4]

