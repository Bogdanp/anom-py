.. anom documentation master file, created by
   sphinx-quickstart on Sat Mar 18 19:48:26 2017.

anom: an om for Cloud Datastore
===============================

Release v\ |release|. (:doc:`changelog`)

**anom** is an object mapper for `Google Cloud Datastore`_ heavily
inspired by `ndb`_ with a focus on simplicity, correctness and
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


.. _Google Cloud Datastore: https://cloud.google.com/datastore/docs/
.. _ndb: https://cloud.google.com/appengine/docs/standard/python/ndb/


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
