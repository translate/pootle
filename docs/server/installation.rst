.. _installation:

Installation
============

Want to try Pootle? This guide will guide you through installing Pootle and its
requirements in a virtual environment.

Before proceeding, consider installing these first:

- Python >= 2.7, < 3.0
- `python-pip <http://www.pip-installer.org/>`_

If you only want to have a sneak peek of Pootle, the default configuration and
the built-in server will suffice. But in case you want to deploy a real world
server, :ref:`installing optional packages <optimization#optional_software>`,
using a real database and :doc:`a proper web server <web>` is highly
recommended.


.. note::

  The easiest way to test and install Pootle is by using pip. However,
  installations can be done straight from git sources or be automated by using
  :ref:`fabric deployment scripts <fabric-deployment>`.


.. _installation#hardware_requirements:

Hardware Requirements
---------------------

Your Pootle installation will need to be flexible enough to handle the
translation load. The recommended hardware depends highly on the performance you
expect, the number of users you want to support, and the number and size of the
files you want to host.

Whatever hardware you have, you will still benefit from performance improvements
if you can :doc:`optimize your system<optimization>`.

Your disk space should always be enough to store your files and your Pootle
database, with some extra space available.


.. _installation#setup_environment:

Setting up the Environment
--------------------------

In order to install Pootle you will first create a virtual environment. This
allows you to keep track of dependencies without messing up with system
packages. For that purpose you need to install the ``virtualenv`` package. You
might already have it, but in case you haven't:

.. code-block:: bash

  $ pip install virtualenv


Now create a virtual environment on your location of choice by issuing the
``virtualenv`` command:

.. code-block:: bash

  $ virtualenv /var/www/pootle/env/


This will copy the system's default Python interpreter into your environment.
For activating the virtual environment you must run the ``activate`` script:

.. code-block:: bash

  $ source /var/www/pootle/env/bin/activate


Every time you activate this virtual environment, the Python interpreter will
know where to look for libraries. Also notice the environment name will be
prepended to the shell prompt.


.. _installation#installing_pootle:

Installing Pootle
-----------------

After creating the virtual environment, you can safely ask pip to grab and
install Pootle by running:

.. code-block:: bash

  (env) $ pip install Pootle


This will fetch and install the minimum set of required dependencies as well.

.. note::

  If you run into trouble while installing the dependencies, it's likely that
  you're missing some extra packages needed to build those third-party packages.

  For example, `lxml <http://lxml.de/installation.html>`_ needs a C compiler.

  lxml also require the development packages of libxml2 and libxslt.

.. note::
   Older versions of pip may try installing pre-release versions of Pootle,
   e.g. installing 2.5.1-rc1 instead of 2.5.1.  In that case run:

   .. code-block:: bash

      (env) $ pip install Pootle==2.5.1


If everything went well, you will now be able to access the ``pootle`` command
line tool within your environment.

.. code-block:: bash

  (env) $ pootle --version
  Pootle 2.5.1
  Translate Toolkit 1.11.0
  Django 1.6.5


.. _installation#initializing_the_configuration:

Initializing the Configuration
------------------------------

Once Pootle has been installed, you will need to initialize a configuration file
for it. This is as easy as running:

.. code-block:: bash

  (env) $ pootle init


By default it writes the configuration file at ``~/.pootle/pootle.conf`` but
if you want you can pass an alternative path as an argument to the ``init``
command.
If the desired path exists, you will be prompted for whether to overwrite the
old configuration. Passing the ``--noinput`` flag assumes a negative answer.

.. warning:: This default configuration is enough to initially experiment with
   Pootle but **it's highly discouraged and unsupported to use this
   configuration in a production environment**.

Also, the default configuration uses SQLite, which shouldn't be used for
anything more than testing purposes.

The initial configuration includes the settings that you're most likely to
change. For further customization, you can also check for the :ref:`full list of
available settings<settings#available>`.


.. _installation#setting_up_the_database:

Setting Up the Database
-----------------------

By default, Pootle uses SQLite as database, which is good enough for testing
purposes.  If you plan to deploy your application in a production environment,
we highly recommend that you use MySQL because it's has been heavily tested. If
you already have data that you would like to migrate from, take a look at our
:doc:`database migration <database_migration>` tutorial.

To use a MySQL database with Pootle, you need to create a new database and
database user. This can be done several different ways (MySQL workbench,
command line, etc.).


We'll show how to do this via command line:

.. code-block:: bash

  mysql -u root -p  #will ask for your root password to log in
  > CREATE DATABASE pootle CHARACTER SET = 'utf8';
  > GRANT ALL PRIVILEGES ON pootle.* TO pootle@localhost IDENTIFIED BY 'passwordhere';
  > FLUSH PRIVILEGES;


.. warning:: **it's highly important** that you set the ``CHARACTER SET`` when
  creating your database. Doing so will eliminate several problems in the future.

Next step, you need to edit ``/home/user/.pootle/pootle.conf`` file and modify
the  ``DATABASES`` dictionary to use your newly created database.

.. code-block:: bash

	DATABASES = {
	    'default': {
	        'ENGINE': 'django.db.backends.mysql',  # Options are sqlite3, mysql, postgresql_psycopg2, oracle
	        'NAME': 'pootle',                      # Or the name you gave to your instance
	        'USER': 'pootle',                      # Or the username you gave when creating it
	        'PASSWORD': 'passwordhere',            # Or the password you assigned when creating it
	        'HOST': '',                            # Set to empty string for localhost
	        'PORT': '',                            # Set to empty string for default
	    }
	}


.. _installation#populating_the_database:

Populating the Database
-----------------------

Before your run Pootle for the first time, you need to create the schema
for the database and populate it with initial data. This is done by
executing the :command:`setup` management command:

.. code-block:: bash

  (env) $ pootle setup


.. note::

   If you are installing directly from the code then you must also build the
   assets after running the previous command:

   .. code-block:: bash

    (env) $ pootle collectstatic --noinput
    (env) $ pootle assets build


.. _installation#running_pootle:

Running Pootle
--------------

By default Pootle provides a built-in `CherryPy server
<http://www.cherrypy.org/>`_ that will be enough for quickly testing the
software. To run it, just issue:

.. code-block:: bash

  (env) $ pootle start


And the server will start listening on port 8000. This can be accessed from your
web browser at ``http://localhost:8000/``.


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

If you plan to run Pootle as a system service, you can use whatever software you
are familiar with for that purpose. For example  `Supervisor
<http://supervisord.org/>`_, `Circus <http://circus.io>`_ or `daemontools
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
