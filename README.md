# anom

[![Build Status](https://travis-ci.org/Bogdanp/anom-py.svg?branch=master)](https://travis-ci.org/Bogdanp/anom-py)
[![Test Coverage](https://codeclimate.com/github/Bogdanp/anom-py/badges/coverage.svg)](https://codeclimate.com/github/Bogdanp/anom-py/coverage)
[![Code Climate](https://codeclimate.com/github/Bogdanp/anom-py/badges/gpa.svg)](https://codeclimate.com/github/Bogdanp/anom-py)
[![PyPI version](https://badge.fury.io/py/anom.svg)](https://badge.fury.io/py/anom)
[![Documentation](https://img.shields.io/badge/doc-latest-brightgreen.svg)](http://anom.defn.io)

**anom** is an object mapper for [Google Cloud Datastore][gcd] heavily
inspired by [ndb][ndb] with a focus on simplicity, correctness and
performance.

Here's what it looks like:

``` python
from anom import Model, props


class Greeting(Model):
  email = props.String(indexed=True, optional=True)
  message = props.Text()
  created_at = props.DateTime(indexed=True, auto_now_add=True)
  updated_at = props.DateTime(indexed=True, auto_now=True)

greeting = Greeting(message="Hi!")
greeting.put()
```

anom is licensed under the 3-clause BSD license and it officially
supports Python 3.6 and later.

## Installation

```
pip install -U anom
```

## Documentation

Documentation is available at http://anom.defn.io.


[gcd]: https://cloud.google.com/datastore/docs/
[ndb]: https://cloud.google.com/appengine/docs/standard/python/ndb/
