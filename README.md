# jq.py: a lightweight and flexible JSON processor

Warning: the API is not stable.

This project contains Python bindings for [jq](http://stedolan.github.io/jq/).

## Examples

```python
from jq import jq

assert [2, 3, 4] == jq("[.[]+1]").transform([1, 2, 3]).json()
assert "[2,3,4]" == str(jq("[.[]+1]").transform([1, 2, 3]))
assert "[2,3,4]" == str(jq("[.[]+1]").transform("[1, 2, 3]", raw=True))
```
