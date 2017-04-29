.. include:: global.rst

Advanced Usage
==============

Models
------

Model Inheritance
^^^^^^^^^^^^^^^^^

By default, entities belonging to model subclasses are stored under
their own kind in datastore::

  class A(Model):
    x = props.String()


  class B(A):
    y = props.Integer()


  a = A(x="hallo").put()
  b = B(x="hallo", y=42).put()

Given the above example, instances of model ``A`` would be stored
under the ``A`` kind and instances of ``B`` under the ``B`` kind.
Querying for either model would look up disjoint sets of data.

Most of the time, this behavior is what you want, but certain use
cases call for multiple models to map to the same kind and that's
where polymorphism comes in.

Polymorphism
^^^^^^^^^^^^

Polymorphic models represent hierarchies of models whose entities are
all stored under the same Datastore kind.

You can declare polymorphic models by setting ``poly`` to ``True``
when you define the root Model.  All children of the root Model will
then be stored under that Model's kind::

  class Animal(Model, poly=True):
    name = props.String()
    born_at = props.DateTime(auto_now_add=True)


  class Bird(Animal):
    flightless = props.Bool(default=False)


  class Eagle(Bird):
    pass


  class Mammal(Animal):
    hairy = props.Boolean(default=True)
    hair_color = props.String()


  class Human(Mammal):
    pass


  class Cat(Mammal):
    pass


  an_eagle = Eagle(name="Goldie").put()
  a_human = Human(name="Jim", hair_color="brown").put()
  a_cat = Cat(name="Sparkles", hair_color="red").put()

In the example above all of the entities will be stored under the
``Animal`` kind in Datastore, along with some additional information
about which specific Model each entity belongs to as well as the set
of parent models of each entity.  Concretely this means that you can
query for all animals::

  >>> list(Animal.query().run())
  [Eagle(...), Human(...), Cat(...)]

and get back a list containing an ``Eagle``, a ``Human`` and a
``Cat``.  Likewise, you can query specifically for all birds or all
eagles and get back an ``Eagle``, excluding all humans or cats::

  >>> list(Bird.query().run())
  [Eagle(...)]

  >>> list(Mammal.query().run())
  [Human(...), Cat(...)]

  >>> list(Human.query().run())
  [Human(...)]


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
Datastore adapter and pass them into a Memcache adapter::

  import pylibmc

  from anom import set_adapter
  from anom.adapters import DatastoreAdapter, MemcacheAdapter

  client = pylibmc.Client(["localhost"], binary=True, {"cas": True})
  datastore_adapter = DatastoreAdapter()
  memcache_adapter = MemcacheAdapter(client, datastore_adapter)

Finally, make the Memcache adapter the global adapter::

  set_adapter(memcache_adapter)

Make sure you require the ``cas`` behavior when you instantiate the
client.

If your application is multi-threaded, the memcache adapter will
handle mapping the client to each thread in a thread-safe manner.
However, if your application forks, you need to ensure that you
instantiate the client and set the adapter *after* forking.

Custom Adapters
^^^^^^^^^^^^^^^

To implement your own adapter, all you need to do is write a class
that implements all of the abstract methods defined on |Adapter|.

Check out the implementations of DatastoreAdapter_ and
MemcacheAdapter_ for examples of this.

.. _DatastoreAdapter: https://github.com/Bogdanp/anom-py/blob/master/anom/adapters/datastore_adapter.py
.. _MemcacheAdapter: https://github.com/Bogdanp/anom-py/blob/master/anom/adapters/memcache_adapter.py
