.. _postgresql_installation:

Installation with PostgreSQL
============================

These instructions provide additional steps for setting up Pootle with
PostgreSQL.

You should read the :ref:`full installation instructions <installation>` in
order to install Pootle.

Pootle supports the :ref:`versions of PostgreSQL supported by Django
<django:postgresql-notes>`, make sure that your installed version is supported.


.. _postgresql_installation#setting-up-db:

Setting up the database
-----------------------

As the ``postgres`` user you must create a database and database user:

.. code-block:: console

   $ sudo su postgres  # On Ubuntu, may be different on your system
   postgres@ $ createuser -P pootle  # This will ask you to define the users password.
   postgres@ $ createdb --encoding='utf8' --locale=en_US.utf8 --template=template0 --owner=pootle pootledb


.. _postgresql_installation#software-requirements:

System software requirements
----------------------------

In addition to the 
:ref:`system packages <requirements#packages>` set out in the general
installation requirements you will also require the PostgreSQL client
development headers in order to build the Python bindings, e.g. on Debian
Jessie:

.. code-block:: console

  $ sudo apt-get install postgresql-server-dev-9.4


.. _postgresql_installation#install-bindings:

Installing PostgreSQL Python bindings
-------------------------------------

Once you have
:ref:`set up and activated your virtual environment <installation#setup-environment>`,
you will need to install the PostgreSQL bindings.

You can do so as follows:

.. code-block:: console

  (env) $ pip install psycopg2


.. _postgresql_installation#init-config:

Initializing the Configuration
------------------------------

When
:ref:`initializing your configuration <installation#initializing-the-configuration>`
you can specify params to set up your database, e.g.:

.. code-block:: console

  (env) $ pootle init --db postgresql --db-name pootledb --db-user pootle

This will create a configuration file to connect to a PostgreSQL database named
``pootledb`` hosted on localhost as the user ``pootle``. Please see the
:djadmin:`init` command for all of the available options.

You will most likely want to edit your Pootle configuration (default location:
:file:`~/.pootle/pootle.conf`) to set your password.


.. _postgresql_installation#db-backend:

Database backend
----------------

Please note that Pootle uses `django-transaction-hooks
<https://pypi.python.org/pypi/django-transaction-hooks/>`_ backends for
connecting to the database. For PostgreSQL the correct :setting:`ENGINE
<DATABASE-ENGINE>` to set for the backend is:

.. code-block:: python

   DATABASES = {
       'default': {
           'ENGINE': 'transaction_hooks.backends.postgresql_psycopg2',
           ...
       }
   }


.. _postgresql_installation#persistent-connections:

A Note on Persistent Connections
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The default value for :setting:`CONN_MAX_AGE <django:DATABASE-CONN_MAX_AGE>` is
``0``. It means that Django creates a connection before every request and closes
it at the end. PostgreSQL supports persistent connections, and it will be fine
to set :setting:`CONN_MAX_AGE <django:DATABASE-CONN_MAX_AGE>` to ``None``.

To learn more please check Django's docs on :ref:`persistent connections and
connection management <django:persistent-database-connections>`.

.. code-block:: python

   DATABASES = {
       'default': {
           ...
           'CONN_MAX_AGE': None,
           ...
       }
   }
