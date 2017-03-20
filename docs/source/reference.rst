API Reference
=============

.. module:: anom


Functions
---------

.. autofunction:: get_adapter
.. autofunction:: set_adapter
.. autofunction:: delete_multi
.. autofunction:: get_multi
.. autofunction:: put_multi
.. autofunction:: lookup_model_by_kind


Keys
----

.. autoclass:: Key
   :members:


Models
------

.. autoclass:: Model
   :members:


Properties
----------

.. autoclass:: Property
   :members:
.. autoclass:: anom.model.NotFound
.. autoclass:: anom.model.Skip

Property Mixins
^^^^^^^^^^^^^^^

.. autoclass:: anom.properties.Blob
.. autoclass:: anom.properties.Compressable
.. autoclass:: anom.properties.Encodable

Built-in Properties
^^^^^^^^^^^^^^^^^^^

.. autoclass:: anom.properties.Bool
.. autoclass:: anom.properties.Bytes
.. autoclass:: anom.properties.Computed
.. autoclass:: anom.properties.DateTime
.. autoclass:: anom.properties.Float
.. autoclass:: anom.properties.Integer
.. autoclass:: anom.properties.Json
.. autoclass:: anom.properties.Key
.. autoclass:: anom.properties.String
.. autoclass:: anom.properties.Text


Queries
-------

.. autoclass:: Query
   :members:
.. autoclass:: Resultset
.. autoclass:: Pages


Query Internals
^^^^^^^^^^^^^^^

.. autoclass:: anom.query.QueryOptions
.. autoclass:: anom.query.PropertyFilter


Adapters
--------

.. autoclass:: anom.Adapter
   :members:

Built-in Adapters
^^^^^^^^^^^^^^^^^

.. autoclass:: anom.adapters.DatastoreAdapter
   :members:

Adapter Internals
^^^^^^^^^^^^^^^^^

.. autoclass:: anom.adapter.PutRequest
.. autoclass:: anom.adapter.QueryResponse


Testing
-------

.. autoclass:: anom.testing.Emulator
   :members:
