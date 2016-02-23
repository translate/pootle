.. _mysql_installation:

Installation with MySQL
=======================

These instructions provide additional steps for setting up Pootle with MySQL.

You should read the :ref:`full installation instructions <installation>` in
order to install Pootle.

Pootle supports the :ref:`versions of MySQL supported by Django
<django:mysql-notes>`, make sure that your installed version is supported.


.. _mysql_installation#setting-up-db:

Setting up the database
-----------------------

Use the :command:`mysql` command to create the user and database:

.. code-block:: console

   $ mysql -u root -p  # You will be asked for the MySQL root password to log in

.. code-block:: sql

   > CREATE DATABASE pootledb CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
   > GRANT ALL PRIVILEGES ON pootledb.* TO pootle@localhost IDENTIFIED BY 'secret';
   > FLUSH PRIVILEGES;


.. _mysql_installation#software-requirements:

System software requirements
----------------------------

In addition to the 
:ref:`system packages <requirements#packages>` set out in the general
installation requirements you will also require the MySQL client
development headers in order to build the Python bindings, e.g. on a
Debian-based system:

.. code-block:: console

  $ sudo apt-get install libmysqlclient-dev


.. _mysql_installation#install-bindings:

Installing MySQL Python bindings
--------------------------------

Once you have
:ref:`set up and activated your virtual environment <installation#setup-environment>`,
you will need to install the MySQL bindings.

You can do so as follows:

.. code-block:: console

  (env) $ pip install MySQL-python


.. _mysql_installation#init-config:

Initializing the Configuration
------------------------------

When
:ref:`initializing your configuration <installation#initializing-the-configuration>`
you can specify params to set up your database, e.g.:

.. code-block:: console

  (env) $ pootle init --db mysql --db-name pootledb --db-user pootle

This will create a configuration file to connect to a MySQL database named
``pootledb`` hosted on localhost as the user ``pootle``. Please see the
:djadmin:`init` command for all of the available options.

You will most likely want to edit your Pootle configuration (default location:
:file:`~/.pootle/pootle.conf`) to set your password.


.. _mysql_installation#db-backend:

Database backend
----------------

Please note that Pootle uses `django-transaction-hooks
<https://pypi.python.org/pypi/django-transaction-hooks/>`_ backends for
connecting to the database. For MySQL the correct :setting:`ENGINE
<django:DATABASE-ENGINE>` to set for the backend is:

.. code-block:: python

   DATABASES = {
       'default': {
           'ENGINE': 'transaction_hooks.backends.mysql',
           ...
       }
   }


.. _mysql_installation#persistent-connections:

A Note on Persistent Connections
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

MySQL terminates idle connections after `wait_timeout
<https://dev.mysql.com/doc/refman/5.5/en/server-system-variables.html#sysvar_wait_timeout>`_
seconds. Thus setting :setting:`CONN_MAX_AGE <django:CONN_MAX_AGE>` to a lower
value will be fine (it defaults to ``0``).  Persistent connections where
:setting:`CONN_MAX_AGE <django:CONN_MAX_AGE>` is ``None`` can't be used with
MySQL.

To learn more please check Django's docs on :ref:`persistent connections and
connection management <django:persistent-database-connections>`.


.. code-block:: python

   DATABASES = {
       'default': {
           ...
           'CONN_MAX_AGE': 0,
           ...
       }
   }
