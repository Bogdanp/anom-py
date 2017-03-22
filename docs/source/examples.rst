Examples
========

Guestbook (Bottle)
------------------

This example uses anom and Bottle_ to build a simple guestbook
application.


.. _Bottle: http://bottlepy.org/docs/dev/index.html

Running
^^^^^^^

To run this example, clone the anom repository to your local machine::

  git clone https://github.com/Bogdanp/anom-py

Then ``cd`` into the ``examples/guestbook`` folder and follow the
instructions in the ``README.md`` file.  To read the un-annotated
source code online click here_.


.. _here: https://github.com/Bogdanp/anom-py/blob/master/examples/guestbook/guestbook.py

Annotated Source Code
^^^^^^^^^^^^^^^^^^^^^

First we import :class:`Model<anom.Model>` and :mod:`props<anom.properties>`
from anom and various Bottle functions:

.. literalinclude:: ../../examples/guestbook/guestbook.py
   :caption: guestbook.py
   :name: guestbook-py-imports
   :start-after: [START imports]
   :end-before: [END imports]

Then we define a ``GuestbookEntry`` model:

.. literalinclude:: ../../examples/guestbook/guestbook.py
   :caption: guestbook.py
   :name: guestbook-py-model
   :start-after: [START guestbook-entry-model]
   :end-before: [END guestbook-entry-model]

``created_at`` has its ``indexed`` option set to ``True`` so that we
can sort guestbook entries in descending order when we list them.
Since the other properties are never used for filtering or sorting,
they are left unindexed.

Next up, we define our index route:

.. literalinclude:: ../../examples/guestbook/guestbook.py
   :caption: guestbook.py
   :name: guestbook-py-index
   :start-after: [START index-route]
   :end-before: [END index-route]

We paginate over the guestbook entry items one item per page for
convenience when testing and we make it possible to pass in a
``cursor`` query parameter.  Bottle returns ``None`` when a query
parameter does not exist which anom interprets as a cursor for the
first page of results.

Then we define a route to create new entries:

.. literalinclude:: ../../examples/guestbook/guestbook.py
   :caption: guestbook.py
   :name: guestbook-py-sign
   :start-after: [START sign-route]
   :end-before: [END sign-route]

And a route to delete existing entries:

.. literalinclude:: ../../examples/guestbook/guestbook.py
   :caption: guestbook.py
   :name: guestbook-py-delete
   :start-after: [START delete-route]
   :end-before: [END delete-route]

Finally, we run the server:

.. literalinclude:: ../../examples/guestbook/guestbook.py
   :caption: guestbook.py
   :name: guestbook-py-run
   :start-after: [START run]
   :end-before: [END run]

Here is the template we used to render the listing:

.. literalinclude:: ../../examples/guestbook/templates/index.html
   :language: html
   :caption: templates/index.html
   :name: guestbook-py-template
