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
.. autofunction:: transactional
.. autofunction:: lookup_model_by_kind


Keys
----

.. autoclass:: Key
   :members:


Models
------

.. autoclass:: Model
   :members:
.. autoclass:: anom.model.model


Properties
----------

.. autoclass:: Property
   :members:

Property Internals
^^^^^^^^^^^^^^^^^^

.. autodata:: anom.model.NotFound
   :annotation:
.. autodata:: anom.model.Skip
   :annotation:

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
.. autoclass:: anom.properties.Msgpack
.. autoclass:: anom.properties.String
.. autoclass:: anom.properties.Text

Built-in Conditions
^^^^^^^^^^^^^^^^^^^

.. autofunction:: anom.conditions.is_default
.. autofunction:: anom.conditions.is_not_default
.. autofunction:: anom.conditions.is_empty
.. autofunction:: anom.conditions.is_not_empty
.. autofunction:: anom.conditions.is_none
.. autofunction:: anom.conditions.is_not_none
.. autofunction:: anom.conditions.is_true
.. autofunction:: anom.conditions.is_false

Queries
-------

.. autoclass:: Query
   :members:
.. autoclass:: Resultset
   :members:
.. autoclass:: Pages
   :members:
.. autoclass:: Page
   :members:


Query Internals
^^^^^^^^^^^^^^^

.. autoclass:: anom.query.QueryOptions
.. autoclass:: anom.query.PropertyFilter


Transactions
------------

.. autoclass:: anom.Transaction
   :members:
.. autoclass:: anom.transaction.TransactionError
.. autoclass:: anom.transaction.TransactionFailed
.. autoclass:: anom.transaction.RetriesExceeded


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
