# jq.py: a lightweight and flexible JSON processor

Warning: the API is not stable.

This project contains Python bindings for [jq](http://stedolan.github.io/jq/).

## Examples

```python
from jq import jq

jq(".").transform("42") == "42"
```

If the value is unparsed JSON text, pass it in using the `text` argument:

```python
jq(".").transform(text="42") == 42
```

The `text_output` argument can be used to serialise the output into JSON text:

```python
jq(".").transform("42", text_output=True) == '"42"'
```

If there are multiple output elements,
each element is represented by a separate line,
irrespective of the value of `multiple_output`:

```python
jq(".[]").transform("[1, 2, 3]", text_output=True) == "1\n2\n3"
```

If `multiple_output` is `False` (the default), then the first output is used:

```python
jq(".[]+1").transform([1, 2, 3]) == 2
```

If `multiple_output` is `True`,
all output elements are returned in an array:

```python
jq(".[]+1").transform([1, 2, 3], multiple_output=True) == [2, 3, 4]
```
