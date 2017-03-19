# anom

**anom** is an object mapper for [Google Cloud Datastore][gcd] heavily
inspired by [ndb][ndb] with a focus on simplicity, correctness and
performance.

Here's what it looks like:

``` python
from anom import Model, props

class Greeting(Model):
  email = props.String(indexed=True, optional=True)
  content = props.Text()
  created_at = props.DateTime(auto_now_add=True)
  updated_at = props.DateTime(auto_now=True)

greeting = Greeting(content="Hi!")
greeting.put()
```

anom officially supports Python 3.6 and later.

## Installation

```
pip install anom
```

## Documentation

Documentation is available at https://anom.readthedocs.io/en/latest/.


[gcd]: https://cloud.google.com/datastore/docs/
[ndb]: https://cloud.google.com/appengine/docs/standard/python/ndb/
