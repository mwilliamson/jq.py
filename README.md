# jq.py: a lightweight and flexible JSON processor

Warning: the API is not stable.

This project contains Python bindings for [jq](http://stedolan.github.io/jq/).

## Examples

```python
from jq import jq

jq(".").transform("42") == "42"
```

The `raw_input` argument can be used to treat the input as a raw JSON string:

```python
jq(".").transform("42", raw_input=True) == 42
```

The `raw_output` argument can be used to serialise the output into a JSON string:

```python
jq(".").transform("42", raw_output=True) == '"42"'
```

The `multiple_output` argument can be used for cases when multiple output elements are expected:

```python
jq(".[]+1").transform([1, 2, 3], multiple_output=True) == [2, 3, 4]
```

If there are multiple output elements, but `multiple_output` is not set to `True`, then the first output is used:

```python
jq(".[]+1").transform([1, 2, 3]) == 2
```
