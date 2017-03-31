.. include:: global.rst

Advanced Usage
==============

Models
------

Model Inheritance
^^^^^^^^^^^^^^^^^

FIXME

Polymorphism
^^^^^^^^^^^^

FIXME


Adapters
--------

Caching Adapters
^^^^^^^^^^^^^^^^

anom provides a Memcached_ adapter (|MemcacheAdapter|) that supports
strongly-consistent caching of datastore entities.  Using this adapter,
you can significantly improve the performance of Datastore lookups, at
the expense of having to run a Memcached server.

To set it up, make sure you've installed anom with the memcache package::

  pip install -U anom[memcache]

Then, in your application instantiate a memcache client and a
Datastore adapter::

  import pylibmc

  from anom import set_adapter
  from anom.adapters import DatastoreAdapter, MemcacheAdapter

  client = pylibmc.Client(["localhost"], binary=True, {"cas": True})
  datastore_adapter = DatastoreAdapter()
  memcache_adapter = MemcacheAdapter(client, datastore_adapter)

Finally, set the global adapter to memcache::

  set_adapter(memcache_adapter)

Make sure you require the ``cas`` behavior when you instantiate the
client.

If your application is multi-threaded, the memcache adapter will
handle mapping the client to each thread in a thread-safe manner.
However, if your application forks you need to ensure that you
instantiate the client and set the adapter *after* forking.

Custom Adapters
^^^^^^^^^^^^^^^

To implement your own adapter, all you need to do is write a class
that implements all of the abstract methods defined on |Adapter|.

Check out the implementations of DatastoreAdapter_ and
MemcacheAdapter_ for examples of this.

.. _DatastoreAdapter: https://github.com/Bogdanp/anom-py/blob/master/anom/adapters/datastore_adapter.py
.. _MemcacheAdapter: https://github.com/Bogdanp/anom-py/blob/master/anom/adapters/memcache_adapter.py
