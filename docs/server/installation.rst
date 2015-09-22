.. _installation:

Installation
============

These instructions will guide you through installing Pootle and its
requirements in a virtual environment.

If you only want to have a sneak peek of Pootle then the default configuration
and the built-in server will suffice.

For a production deployment we **strongly** recommend that you set up the following:

- :ref:`Install optional optimization packages<optimization#optional_software>`
- Use either a :ref:`MySQL <mysql_installation>`
  or :ref:`PostgreSQL <postgresql_installation>` database.
- :doc:`Make use of a front-end web server <web>`


.. note:: Before installing please ensure that you have all the
   :ref:`necessary requirements <requirements>`.


.. _installation#assumptions:

Setup assumptions
-----------------

We've made some assumptions in these instructions, adjust as needed:

#. All of the :ref:`Pootle requirements <requirements#packages>` have been
   installed.
#. We're installing into :file:`~/dev/pootle`.
#. We're using SQLite as it's easy to setup.
#. We're setting up the essential parts of Pootle including Redis, and RQ
   Workers.
#. This is a test installation on a single server, and not optimised for
   production use.
#. We're installing using :command:`pip`.


.. _installation#setup-environment:

Setting up the virtual environment
----------------------------------

In order to install Pootle first create a virtual environment. The virtual
environment allows you to install dependencies independent of your system
packages. 

Please install ``virtualenv`` from your system packages, e.g. on Debian:

.. code-block:: bash

  $ sudo apt-get install python-virtualenv


Otherwise you can install ``virtualenv`` using :command:`pip`:

.. code-block:: bash

  $ sudo pip install virtualenv


Now create a virtual environment on your location of choice by issuing the
``virtualenv`` command:

.. code-block:: bash

  $ cd ~/dev/pootle
  $ virtualenv env


To activate the virtual environment run the :command:`activate` script:

.. code-block:: bash

  $ source env/bin/activate

Once activated the virtual environment name will be prepended to the shell prompt.

Lastly, we want to make sure that we are using the latest version of
:command:`pip`:

.. code-block:: bash

   (env) $ pip install --upgrade pip


.. _installation#installing-pootle:

Installing Pootle
-----------------

Use :command:`pip` to install Pootle into the virtual environment:

.. code-block:: bash

  (env) $ pip install Pootle


This will also fetch and install Pootle's dependencies.

To verify that everything installed correctly, you should be able to access the
:command:`pootle` command line tool within your environment.

.. code-block:: bash

  (env) $ pootle --version
  Pootle 2.7.1 (Django 1.7.10, Translate Toolkit 1.13.0)


.. _installation#initializing-the-configuration:

Initializing the Configuration
------------------------------

Once Pootle has been installed, you will need to initialize a configuration
file:

.. code-block:: bash

  (env) $ pootle init

By default the configuration file is saved as :file:`~/.pootle/pootle.conf`. You can pass
an alternative path as an argument if required - see the :djadmin:`init` command for all
of the options.

.. warning:: This default configuration is enough to experiment with Pootle.
   **Don't use this configuration in a production environment**.

The initial configuration includes the settings that you're most likely to
change. For further customization, see the :ref:`full list of available
settings <settings#available>`.


.. _installation#running-rqworker:

Running RQ worker
-----------------

Statistics tracking and various other background processes are managed by `RQ
<http://python-rq.org/>`_.  The :djadmin:`rqworker` command needs to be run
continuously in order to process the jobs.

If you have not already done so you should
:ref:`install and start a Redis server <requirements#packages>`.

You can start the worker in the background with the following command:

.. code-block:: bash

   (env) $ pootle rqworker &

In a production environment you may want to :ref:`run RQ workers as services
<pootle#running_as_a_service>`.

See here for :ref:`further information about RQ jobs in Pootle <rq>`.


.. _installation#populating-the-database:

Populating the Database
-----------------------

Before you run Pootle for the first time, you need to create the schema for
the database and populate it with initial data. This is done by executing the
:djadmin:`migrate` and :djadmin:`initdb` management commands:

.. code-block:: bash

  (env) $ pootle migrate
  (env) $ pootle initdb


.. _installation#refreshing-stats:

Refreshing stats
----------------

On first installation you will need to generate the statistics from your
database. You will need to have an :ref:`RQ worker running 
<installation#running-rqworker>` to complete this.

.. code-block:: bash

   (env) $ pootle refresh_stats

This command will dispatch jobs to the RQ worker and may take some time.

If you wish to run :djadmin:`refresh_stats` in the foreground without using the RQ
worker you can use the :option:`--no-rq` option.


.. _installation#admin-user:

Creating an admin user
----------------------

Pootle needs at least one user with superuser rights which we create with the
:djadmin:`createsuperuser` command.

.. code-block:: bash

  (env) $ pootle createsuperuser


All users are required to verify their email before logging in. If you wish to
bypass this step you can use the :djadmin:`verify_user` command.

For example to allow a user named ``admin`` to log in without having to verify
their email address:

.. code-block:: bash

  (env) $ pootle verify_user admin


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


.. _installation#next-steps:

Next steps
----------

Now that you have Pootle up and running you may want to consider some of the
following in order to build a production environment.

- :ref:`Run Pootle and RQ workers as services <pootle#running_as_a_service>`
- :ref:`Set up a reverse-proxy web server for static files <apache#reverse_proxy>`
- :ref:`Use a wsgi server to serve dynamic content <apache#mod_wsgi>`
- :ref:`Check out the available settings <settings#available>`
- :ref:`Check out Pootle management commands <commands>`
- :doc:`Optimize your setup <optimization>`
- :ref:`Set up a Translation Memory Server <translation_memory>`
- :ref:`Customize the Pootle UI <customization>`
