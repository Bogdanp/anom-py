.. include:: global.rst

anom: an om for Cloud Datastore
===============================

Release v\ |release|. (:doc:`installation`, :doc:`changelog`)

.. image:: https://img.shields.io/badge/license-BSD--3-blue.svg
   :target: license.html
.. image:: https://travis-ci.org/Bogdanp/anom-py.svg?branch=master
   :target: https://travis-ci.org/Bogdanp/anom-py
.. image:: https://coveralls.io/repos/github/Bogdanp/anom-py/badge.svg?branch=master
   :target: https://coveralls.io/github/Bogdanp/anom-py?branch=master
.. image:: https://api.codacy.com/project/badge/Grade/a4d2fc43036b4277bf196de6f1766fd7
   :target: https://www.codacy.com/app/bogdan/anom-py?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Bogdanp/anom-py&amp;utm_campaign=Badge_Grade
.. image:: https://badge.fury.io/py/anom.svg
   :target: https://badge.fury.io/py/anom
.. image:: https://img.shields.io/badge/Say%20Thanks!-%F0%9F%A6%89-1EAEDB.svg
   :target: https://saythanks.io/to/Bogdanp

**anom** is an object mapper for `Google Cloud Datastore`_ heavily
inspired by ndb_ with a focus on simplicity, correctness and
performance.

Here's what it looks like:

::

   from anom import Model, props

   class Greeting(Model):
     email = props.String(indexed=True, optional=True)
     message = props.Text()
     created_at = props.DateTime(auto_now_add=True)
     updated_at = props.DateTime(auto_now=True)

   greeting = Greeting(message="Hi!")
   greeting.put()

**anom** is :doc:`licensed<license>` under the 3-clause BSD license
and it officially supports Python 3.6 and later.

.. warning::

   anom is under heavy development and is currently not ready for
   prodution use.

Get It Now
----------

::

   $ pip install -U anom

Read the :doc:`quickstart` if you're ready to get started or check out
some of the :doc:`examples`.


User Guide
----------

This part of the documentation is focused primarily on teaching you
how to use anom.

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   examples
   advanced


API Reference
-------------

This part of the documentation is focused on detailing the various
bits and pieces of the anom developer interface.

.. toctree::
   :maxdepth: 2

   reference


Project Info
------------

.. toctree::
   :maxdepth: 1

   changelog
   license
