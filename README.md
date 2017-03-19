# anom

[![Build Status](https://travis-ci.org/Bogdanp/anom-py.svg?branch=master)](https://travis-ci.org/Bogdanp/anom-py)
[![Coverage Status](https://coveralls.io/repos/github/Bogdanp/anom-py/badge.svg?branch=master)](https://coveralls.io/github/Bogdanp/anom-py?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/a4d2fc43036b4277bf196de6f1766fd7)](https://www.codacy.com/app/bogdan/anom-py?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Bogdanp/anom-py&amp;utm_campaign=Badge_Grade)
[![PyPI version](https://badge.fury.io/py/anom.svg)](https://badge.fury.io/py/anom)
[![Documentation Status](https://readthedocs.org/projects/anom/badge/?version=latest)](http://anom.readthedocs.io/en/latest/?badge=latest)

**anom** is an object mapper for [Google Cloud Datastore][gcd] heavily
inspired by [ndb][ndb] with a focus on simplicity, correctness and
performance.

Here's what it looks like:

``` python
from anom import Model, props

class Greeting(Model):
  email = props.String(indexed=True, optional=True)
  message = props.Text()
  created_at = props.DateTime(auto_now_add=True)
  updated_at = props.DateTime(auto_now=True)

greeting = Greeting(message="Hi!")
greeting.put()
```

anom is licensed under the 3-clause BSD license and it officially
supports Python 3.6 and later.

## Installation

```
pip install anom
```

## Documentation

Documentation is available at https://anom.readthedocs.io/en/latest/.


[gcd]: https://cloud.google.com/datastore/docs/
[ndb]: https://cloud.google.com/appengine/docs/standard/python/ndb/
