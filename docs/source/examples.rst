.. include:: global.rst

Examples
========

Guestbook (Bottle)
------------------

This example uses anom and Bottle_ to build a simple guestbook
application.


Running
^^^^^^^

To run this example, clone the anom repository to your local machine::

  git clone https://github.com/Bogdanp/anom-py

Then ``cd`` into the ``examples/guestbook`` folder and follow the
instructions in the ``README.md`` file.  To read the un-annotated
source code online click here__.


.. __: https://github.com/Bogdanp/anom-py/blob/master/examples/guestbook/guestbook.py

Annotated Source Code
^^^^^^^^^^^^^^^^^^^^^

First we import |Model| and |props| from |anom| and various bottle_
functions:

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


Blog (Bottle)
-------------

This example uses anom and Bottle_ to build a simple blog.


Running
^^^^^^^

To run this example, clone the anom repository to your local machine::

  git clone https://github.com/Bogdanp/anom-py

Then ``cd`` into the ``examples/blog`` folder and follow the
instructions in the ``README.md`` file.  To read the un-annotated
source code online click here__.


.. __: https://github.com/Bogdanp/anom-py/blob/master/examples/blog

Annotated Source Code
^^^^^^^^^^^^^^^^^^^^^

Models
++++++

In order to make password hashing transparent, we define a custom
``Password`` property that hashes values automatically every time
they are assigned to an entity.

.. literalinclude:: ../../examples/blog/models.py
   :caption: models.py
   :name: blog-models-py-password
   :start-after: [START password-property]
   :end-before: [END password-property]

Then we declare a polymorphic user model.  Polymorphic models allow us
to define class hierarchies that are all stored under the same
Datastore kind, this means that ``User`` entities and entities of its
subclasses will each be stored under the ``User`` kind in Datastore
(as opposed to standard inheritance, where each subclass would get its
own kind).

.. literalinclude:: ../../examples/blog/models.py
   :caption: models.py
   :name: blog-models-py-user
   :start-after: [START user-model]
   :end-before: [END user-model]

Next, we define ``Editor`` and ``Reader`` users:

.. literalinclude:: ../../examples/blog/models.py
   :caption: models.py
   :name: blog-models-py-editor-and-reader
   :start-after: [START editor-and-reader-models]
   :end-before: [END editor-and-reader-models]

And a model for ``Post`` entities:

.. literalinclude:: ../../examples/blog/models.py
   :caption: models.py
   :name: blog-models-py-post
   :start-after: [START post-model]
   :end-before: [END post-model]

The repreated ``tags`` property on posts is there so that we can
filter post queries by one or many tags at a time.

Finally, we define and call a method to populate the database with an
editor and a reader user on first run:

.. literalinclude:: ../../examples/blog/models.py
   :caption: models.py
   :name: blog-models-init
   :start-after: [START init-database]
   :end-before: [END init-database]

Sessions
++++++++

We define a ``Session`` model that is used to assign random session
ids to individual users when they login.

.. literalinclude:: ../../examples/blog/session.py
   :caption: session.py
   :name: blog-session-model
   :start-after: [START session-model]
   :end-before: [END session-model]

Here we use the ``uuid4`` function to generate random session ids and
assign them as custom ids to new ``Session`` entities.  This way we
can store the session id on the user's computer using a cookie and
then read that cookie back to look up the session via a |Model_get|
call rather than a |Query| in the ``user_required`` decorator:

.. literalinclude:: ../../examples/blog/session.py
   :caption: session.py
   :name: blog-session-user-required
   :start-after: [START user-required]
   :end-before: [END user-required]

Finally we define a helper for creating ``Session`` objects and
setting the session id cookie:

.. literalinclude:: ../../examples/blog/session.py
   :caption: session.py
   :name: blog-session-create-session
   :start-after: [START create-session]
   :end-before: [END create-session]

Routes
++++++

We define a route to list blog posts, optionally allowing them to be
filtered by `tag`:

.. literalinclude:: ../../examples/blog/blog.py
   :caption: blog.py
   :name: blog-py-index
   :start-after: [START index]
   :end-before: [END index]

And a route that lets users view individual posts by `slug`:

.. literalinclude:: ../../examples/blog/blog.py
   :caption: blog.py
   :name: blog-py-post
   :start-after: [START post]
   :end-before: [END post]

One that lets users with ``create`` permissions to create posts:

.. literalinclude:: ../../examples/blog/blog.py
   :caption: blog.py
   :name: blog-py-create
   :start-after: [START create]
   :end-before: [END create]

And one that logs users in.  This is the route anonymous users are
taken to when they visit routes that have been decorated with
``user_required``.

.. literalinclude:: ../../examples/blog/blog.py
   :caption: blog.py
   :name: blog-py-login
   :start-after: [START login]
   :end-before: [END login]

Finally, we run the server:

.. literalinclude:: ../../examples/blog/blog.py
   :caption: blog.py
   :name: blog-py-run
   :start-after: [START run]
   :end-before: [END run]
