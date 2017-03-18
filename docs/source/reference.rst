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


Models and Keys
---------------

.. autoclass:: Key
   :members:
.. autoclass:: Model
   :members:


Properties
----------

.. autoclass:: Property
   :members:


Property mixins
^^^^^^^^^^^^^^^

.. autoclass:: anom.properties.Blob
.. autoclass:: anom.properties.Compressable
.. autoclass:: anom.properties.Encodable


Built-in properties
^^^^^^^^^^^^^^^^^^^

.. autoclass:: anom.properties.Bool
.. autoclass:: anom.properties.Bytes
.. autoclass:: anom.properties.DateTime
.. autoclass:: anom.properties.Float
.. autoclass:: anom.properties.Integer
.. autoclass:: anom.properties.Json
.. autoclass:: anom.properties.Key
.. autoclass:: anom.properties.String
.. autoclass:: anom.properties.Text


Adapters
--------

.. autoclass:: anom.Adapter
   :members:


Built-in adapters
^^^^^^^^^^^^^^^^^

.. autoclass:: anom.adapters.DatastoreAdapter
   :members:


Adapter internals
^^^^^^^^^^^^^^^^^

.. autoclass:: anom.adapter.PutRequest


Testing utilities
-----------------

.. autoclass:: anom.testing.Emulator
   :members:
