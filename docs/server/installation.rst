.. _installation:

Installation
============

These instructions will guide you through installing Pootle and its
requirements in a virtual environment.

If you only want to have a sneak peek of Pootle then the default configuration
and the built-in server will suffice. But in case you want to deploy a real
world server, :ref:`installing optional packages
<optimization#optional_software>`, using a real database and :doc:`a proper web
server <web>` is highly recommended.

The easiest way to test and install Pootle is by using pip, however,
installating it straight from git sources is another viable approach.


.. _installation#requirements:

Requirements
------------


.. _installation#hardware_requirements:

Hardware Requirements
^^^^^^^^^^^^^^^^^^^^^

Your Pootle installation will need to be flexible enough to handle the
translation load. The recommended hardware depends highly on the performance you
expect, the number of users you want to support, and the number and size of the
files you want to host.

Whatever hardware you have, you will still benefit from performance improvements
if you can :doc:`optimize your system <optimization>`.

Your disk space should always be enough to store your files and your Pootle
database, with some extra space available.


.. _installation#system_requirements:

System Requirements
^^^^^^^^^^^^^^^^^^^

To run Pootle you need a computer running:

- Linux
- Mac OS X

Or, any other Unix-like system.

.. note:: Pootle will not run on Windows since it uses RQ, whose workers cannot
   run on `Windows <http://python-rq.org/docs/>`_.

   Some developers do develop on Windows so these problems can be worked around
   for some of the development tasks.

   Pootle should be able to run on any system that implements ``fork()``.


Software requirements
^^^^^^^^^^^^^^^^^^^^^

**Python 2.7 is required**. 2.6 won't work, and 3.x is not supported.

You will also need the following system services for a working Pootle:

- Redis - all caching and managing of workers uses Redis
- Database - MySQL or PostgreSQL (although for testing SQLite is fine)
- Elasticsearch (optional) - for Local Translation Memory

These are preferably installed from system packages.


.. _installation#assumptions:

Setup assumptions
-----------------

We've made some assumptions in these instructions, adjust as needed:

#. We're installing into :file:`~/dev/pootle`.  For a deployment you'd want to
   run this from the webserver directory.
#. We're using SQLite as its easy to setup. Though we do include instructions
   for quickly setting up MySQL or PostgreSQL.
#. We're setting up the key parts of Pootle including Redis, Workers and Local
   TM.
#. This is a test installation.  We're not setting up a server for hosting or
   optimising in any way.
#. We're installing using :command:`pip`. There are also
   :ref:`instructions for setting up Pootle using a git checkout
   <installation#git>`.


.. _installation#setup_environment:

Setting up the virtual environment
----------------------------------

In order to install Pootle first create a virtual environment. The virtual
environment allows you to install dependencies independent of your system
packages. For this purpose you need to install the ``virtualenv`` package.
Preferably install it from your system packages.  Otherwise use :command:`pip`:

.. code-block:: bash

  $ pip install virtualenv


Now create a virtual environment on your location of choice by issuing the
``virtualenv`` command:

.. code-block:: bash

  $ cd ~/dev/pootle
  $ virtualenv env


To activate the virtual environment run the :command:`activate` script:

.. code-block:: bash

  $ source env/bin/activate


With an activated virtual environment, Python will look within the virtual
environment for Python libraries. Note that the virtual environment name will
be prepended to the shell prompt.

Lastly, we want to make sure that we are using the latest version of
:command:`pip`:

.. code-block:: bash

   (env) $ pip install --upgrade pip


.. _installation#installing_pootle:

Installing Pootle
-----------------

Use :command:`pip` to install Pootle into the virtualenv:

.. code-block:: bash

  (env) $ pip install Pootle


This will also fetch and install a minimum set of dependencies.

.. note::
  Most issues encountered when installing the dependencies relate to missing
  development packages needed to build the 3rd party packages.

  For example, `lxml <http://lxml.de/installation.html>`_ needs a C compiler.

  lxml also require the development packages of libxml2 and libxslt.
  Depending on your system these may be the ``libxml2-dev`` and ``libxslt-dev``
  packages.


To verify that everything installed correctly, you should be able to access the
:command:`pootle` command line tool within your environment.

.. code-block:: bash

  (env) $ pootle --version
  Pootle 2.7.0 (Django 1.7.8, Translate Toolkit 1.13.0)


.. _installation#git:

Installation from a Git Checkout
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An alternative to installing from a package is to install directly from Git.
This is useful if you are developing Pootle or if you want to have a fine
control when updating a server.

Checkout and install the Pootle source code:

.. code-block:: bash

   (env) $ git clone https://github.com/translate/pootle.git
   (env) $ cd pootle
   (env) $ pip install .

Alternatively, if you want your install to be live use ``pip install -e
.``. In this case any changes your make in the repository will be
available to Pootle.


.. _installation#initializing_the_configuration:

Initializing the Configuration
------------------------------

Once Pootle has been installed, you will need to initialize a configuration
file as follows:

.. code-block:: bash

  (env) $ pootle init


This writes the configuration file to ``~/.pootle/pootle.conf``. You can pass
an alternative path as an argument if required.

.. warning:: This default configuration is enough to experiment with Pootle.
   **Don't use this configuration in a production environment**.

You can specify the parameters to set up your database if you don't want to use
the default setup, see the :djadmin:`init command <init>` for the
available options.

The initial configuration includes the settings that you're most likely to
change. For further customization, see the :ref:`full list of available
settings <settings#available>`.


.. _installation#setting_up_the_database:

Setting Up the Database
-----------------------

By default, Pootle will use SQLite as its database, which is good enough for
testing purposes.

If you are using SQLite then skip to :ref:`Populating the Database
<installation#populating_the_database>`.

If you want to migrate to a supported database, then read the
:doc:`database migration <database_migration>` tutorial.

If you plan to deploy to a production environment then we highly recommend that
you use MySQL or PostgreSQL (MySQL has been most heavily tested).

In this section we are creating a database user for Pootle called ``pootle``
with a password of ``secret`` and a Pootle dabatase named ``pootledb``.

.. warning:: **It is critical** that you set the character set, or encoding, to
   UTF-8 when creating your database.  It is most likely that a target language
   on Pootle will require Unicode to represent the characters.  Pootle itself
   assumes Unicode throughout.


.. _installation#mysql:

MySQL
^^^^^

Use the :command:`mysql` command to create the user and database:

.. code-block:: bash

   $ mysql -u root -p  # You will be asked for the MySQL root password to log in

.. code-block:: sql

   > CREATE DATABASE pootledb CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
   > GRANT ALL PRIVILEGES ON pootledb.* TO pootle@localhost IDENTIFIED BY 'secret';
   > FLUSH PRIVILEGES;


.. _installation#postgresql:

PostgreSQL
^^^^^^^^^^

Use the :command:`psql` command to create a user and database:

.. code-block:: bash

   $ sudo su postgres  # On Ubuntu, may be different on your system
   postgres@ $ createuser -P pootle  # This will ask you to define the users password.
   postgres@ $ createdb --encoding='utf-8' --locale=en_US.utf8 --template=template0 --owner=pootle pootledb


.. _installation#database_backends:

Database backends
-----------------

.. warning:: Pootle now requires django-transaction-hooks.
   **You should update your database backend if migrating from a version older than 2.7.1**


Following the database creation, you need to modify the :setting:`DATABASES`
setting appropriately in your custom settings file, ensuring that you are using
the correct :setting:`ENGINE <DATABASE-ENGINE>` setting for your chosen
database backend.

Pootle requires `django-transaction-hooks <https://pypi.python.org/pypi/django-transaction-hooks/>`_
to connect to the database. The following database backends are supported:

- mysql: transaction_hooks.backends.mysql
- postgres: transaction_hooks.backends.postgresql_psycopg2

.. _installation#populating_the_database:

Populating the Database
-----------------------

Before you run Pootle for the first time, you need to create the schema for
the database and populate it with initial data. This is done by executing the
:djadmin:`migrate` and :djadmin:`initdb` management commands:

.. code-block:: bash

  (env) $ pootle migrate
  (env) $ pootle initdb


.. _installation#admin_user:

Creating an admin user
----------------------

Pootle needs at least one user with superuser rights which we create with the
:djadmin:`createsuperuser` command.

.. code-block:: bash

  (env) $ pootle createsuperuser


.. _installation#static_assets:

Static Assets
-------------

If you are installing Pootle via pip you can skip this step.

In case you are using a git clone, then you must also build the static
assets (note you need Node.js and npm for this):

.. code-block:: bash

   (env) $ cd pootle/static/js
   (env) $ npm install
   (env) $ cd ../../..
   (env) $ make assets


.. _installation#background_services:

Background services
-------------------

Pootle stores various cached data in a `Redis <http://redis.io/>`_ server.  You
need to install Redis as required for your operating system or distribution.

On Ubuntu this would be as follows:

.. code-block:: bash

   $ sudo apt-get install redis-server
   $ sudo services redis-server start


.. _installation#background_processes:

Background processes
--------------------

Statistics counting and various other background processes are managed by `RQ
<http://python-rq.org/>`_.  The :djadmin:`rqworker` command needs to be run
continuously in the background in order to process the jobs.

.. code-block:: bash

   (env) $ pootle rqworker


.. _installation#running_pootle:

Running Pootle
--------------

By default Pootle provides a built-in `CherryPy server
<http://www.cherrypy.org/>`_ that will be enough for quickly testing the
software. To run it, just issue:

.. code-block:: bash

   (env) $ pootle start


And the server will start listening on port 8000. This can be accessed from
your web browser at `localhost:8000 <http://localhost:8000/>`_.


.. _installation#reverse_proxy:

Setting up a Reverse Proxy
--------------------------

By default the Pootle server runs on port 8000 and you will probably be
interested on binding it to the usual port 80. Also, it's highly recommended to
have all the static assets served by a proper web server, and setting up a web
proxy is the simplest way to go.

The :ref:`web` section has further information on setting up a web server that
proxyes requests to the application server.

If you want to omit a reverse proxy and rather prefer to use a web server for
serving both dynamic and static content, you can also setup such a scenario with
:ref:`Apache and mod_wsgi <apache#mod_wsgi>` for example.


.. _installation#running_as_a_service:

Running Pootle as a Service
---------------------------

If you plan to run Pootle as a system service, you can use whatever software
you are familiar with for that purpose. For example  `Supervisor
<http://supervisord.org/>`_, `Circus
<http://circus.readthedocs.org/en/latest/>`_ or `daemontools
<http://cr.yp.to/daemontools.html>`_ might fit your needs.


.. _installation#additional:

Further Configuration and Tuning
--------------------------------

This has been a quickstart for getting you up and running. If you want to
continue diving into Pootle, you should first consider :doc:`making some
optimizations to your setup <optimization>` — don't forget to switch your
database backend! After that you should also :doc:`adjust the application
configuration <settings>` to better suit your specific needs.

For additional scripting and improved management, Pootle also provides a set of
:ref:`management commands <commands>` to ease the automation of common
administration tasks.

You might also want to create a :ref:`Local Translation Memory
<translation_memory#local_translation_memory>`.
