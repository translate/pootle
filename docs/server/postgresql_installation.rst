.. _postgresql_installation:

Installation with PostgreSQL
============================

These instructions provide additional steps for setting up Pootle with
PostgreSQL.

You should read the :ref:`full installation instructions <installation>` in
order to install Pootle.


.. _postgresql_installation#setting-up-db:

Setting up the database
-----------------------

As the ``postgres`` user you must create a database and database user:

.. code-block:: bash

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

.. code-block:: bash

  $ sudo apt-get install postgresql-server-dev-9.4


.. _postgresql_installation#install-bindings:

Installing PostgreSQL Python bindings
-------------------------------------

Once you have
:ref:`set up and activated your virtual environment <installation#setup-environment>`,
you will need to install the PostgreSQL bindings.

You can do so as follows:

.. code-block:: bash

  (env) $ pip install psycopg2


.. _postgresql_installation#init-config:

Initializing the Configuration
------------------------------

When
:ref:`initializing your configuration <installation#initializing-the-configuration>`
you can specify params to set up your database, e.g.:

.. code-block:: bash

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
connecting to the database. For PostgreSQL the correct ``ENGINE`` to set for
the backend is:

.. code-block:: python

   DATABASES = {
       'default': {
           'ENGINE': 'transaction_hooks.backends.postgresql_psycopg2',
           ...
       }
   }
