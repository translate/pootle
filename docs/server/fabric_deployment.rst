.. _fabric-deployment:

Automated deployment using Fabric
=================================

Pootle can be deployed using Fabric automation scripts. There are other methods
to deploy Pootle, perhaps simpler, but this one is intended to perform automated
deployments that ease its maintenance tasks and the upgrade to newer versions.

The sample scripts bundled with Pootle allow to deploy a Pootle server within a
virtual environment, running in a **Apache** server with *mod_wsgi* using
**MySQL** as database server in **Debian** systems. This sample scripts can be
changed to perform different deployments.

To see a comprehensive list of all Fabric commands available to deploy Pootle
check the :ref:`Fabric commands reference <fabric-commands>`.


.. _fabric-deployment#preparing-the-remote-server:

Preparing the remote server
---------------------------

Before performing an automated deployment using Fabric it is necessary that the
server where Pootle is going to be deployed is ready to perform that deployment.


.. _fabric-deployment#installing-required-software-on-the-remote-server:

Installing required software on the remote server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before proceeding, consider installing the following software first on the
remote server:

- At least Python 2.5
- `python-pip <http://www.pip-installer.org/>`_
- Git distributed version control system
- Apache web server
- MySQL database server
- OpenSSH server

.. note:: Currently only Debian like remote servers are supported.

.. note:: If you run into trouble while installing the dependencies, it's likely
  that you're missing some extra packages needed to build those third-party
  packages. For example, `lxml <http://lxml.de/installation.html>`_ needs a C
  compiler.

.. note:: Also consider :ref:`installing optional packages
   <optimization#optional_software>` for optimal performance.


.. _fabric-deployment#hardware_requirements:

Hardware requirements
^^^^^^^^^^^^^^^^^^^^^

Check the :ref:`Hardware requirements <installation#hardware_requirements>` on
Installation docs.


.. _fabric-deployment#preparing-fabric-deployment:

Preparing Fabric deployment
---------------------------

Before performing the deployment it is necessary to install some software on the
local computer and set up the necessary settings to connect to the remote
server.


.. _fabric-deployment#installing-required-software-on-the-local-computer:

Installing required software on the local computer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first step is to install the necessary software on the local computer.

.. note:: We strongly recommend using a virtual environment. Check the
   :ref:`Setting up the Environment <installation#setup_environment>` docs to
   see how to set up a virtual environment.

.. code-block:: bash

    $ pip install Fabric


.. _fabric-deployment#getting-pootle-fabric-files:

Getting Pootle Fabric files
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pootle is bundled with sample scripts for deploying using Fabric. The relevant
files are:

- :file:`fabfile.py`
- Files inside the :file:`deploy/` directory

So grab those files from `Pootle Github repository
<https://github.com/translate/pootle>`_. The rest of Pootle files are not
necessary for this kind of deployment.


.. _fabric-deployment#setting-up-fabric:

Setting up Fabric
^^^^^^^^^^^^^^^^^

The :file:`deploy/` directory contains sample files that can be used in
combination with the :file:`fabfile.py` file for deploying Pootle servers.

There are two different deployment environments. Each one has a directory inside
:file:`deploy/`:

- Staging environment: :file:`deploy/staging/` directory
- Production environment: :file:`/deploy/production/` directory

This way server administrators can separate their testing and real-world Pootle
servers.

For deploying a Pootle server using one of the environments it is necessary to
put some configuration files in place:

- :file:`/deploy/ENVIRONMENT/fabric.py` 
  Module with settings that will be used in Fabric.

- :file:`/deploy/ENVIRONMENT/settings.conf`
  Pootle-specific settings for the server (it will override the defaults). For
  example, include here the settings for connecting to the DB.

- :file:`/deploy/ENVIRONMENT/virtualhost.conf`
  Apache VirtualHost configuration file.

In the previous paths ``ENVIRONMENT`` is the directory name for the chosen
environment.

All the settings defined in the :file:`/deploy/ENVIRONMENT/fabric.py` module
will populate the Fabric ``env`` dictionary, making the configuration keys
available in the :file:`/deploy/ENVIRONMENT/settings.conf` and
:file:`/deploy/ENVIRONMENT/virtualhost.conf` files. You can use basic Python
string formatting to access the configuration values.

Sample configuration files are provided for reference under the :file:`/deploy/`
directory. Put them in the desired environment directory, and adapt them to your
needs before running any Fabric commands.

Check :file:`pootle/settings/90-local.conf.sample` to see settings that you
might want to use in :file:`/deploy/ENVIRONMENT/settings.conf`.

Once you make all the necessary changes in the settings you are ready to run the
Fabric commands.

.. note:: For security reasons, please make sure you change the settings in
   order to not ressemble like the default ones.


.. _fabric-deployment#bootstrap-environment:

Bootstraping the environment
----------------------------

.. code-block:: bash

    $ export PYTHONPATH=`pwd`:$PYTHONPATH
    $ fab production bootstrap:branch=stable/2.5.0  # Install Pootle

.. note:: Exporting the ``PYTHONPATH`` won't be necessary if the current
   directory already is on PYTHONPATH.


.. _fabric-deployment#setting-up-the-database:

Setting Up the Database
-----------------------

If updating a previous DB to last version schema:

.. code-block:: bash

    $ fab production update_db  # Updates DB schema to last version

If creating a blank DB and populating with a DB backup:

.. code-block:: bash

    $ fab production create_db  # Creates Pootle DB on MySQL
    $ fab production load_db:dumpfile=backup_mysql.sql # Populates the DB using a dump


.. _fabric-deployment#enabling-the-web-server:

Enabling the web server
-----------------------

.. code-block:: bash

    $ fab production deploy:branch=stable/2.5.0


.. _fabric-deployment#how-to-run-commands:

How to run commands
-------------------

In order to run a Fabric command for Pootle it is necessary that the directory
where the :file:`fabfile` lives is in the ``PYTHONPATH``. If not then add it
using:

.. code-block:: bash

    $ export PYTHONPATH=`pwd`:$PYTHONPATH

The commands require some setup in order to know in which type of environment
they are going to work. For example if the deploy would be on a production
environment. Pootle includes two sample environments: ``production`` and
``staging``. To set up the environment before running a command just add it
before the command like in:

.. code-block:: bash

    $ fab production bootstrap  # Use the 'production' environment
    $ fab staging bootstrap  # Or use the 'staging' environment

.. note:: It is necessary to :ref:`install Fabric 
   <fabric-deployment#installing-required-software-on-the-local-computer>` in
   order to be able to run the :command:`fab` command.

Some commands accept options:

.. code-block:: bash

    $ fab production bootstrap:branch=stable/2.5.0  # Call bootstrap providing a branch

The previous call runs the :ref:`bootstrap <fabric-commands#bootstrap>` command
providing the value ``stable/2.5.0`` for its :option:`branch` option.

It is also possible to run several commands in a row with a single call.

.. code-block:: bash

    $ # Run several commands in a row using a single call to fab
    $ fab production bootstrap:branch=stable/2.5.0 create_db load_db:dumpfile=backup_mysql_2.5.0-rc1.sql

The previous call will run :ref:`production <fabric-commands#production>`
followed by :ref:`bootstrap <fabric-commands#bootstrap>`, :ref:`create_db
<fabric-commands#create-db>` and :ref:`load_db <fabric-commands#load-db>`, in
that exact order.

.. note:: If you want to know more about Fabric, please read `its documentation
   <http://docs.fabfile.org/en/latest/>`_.

Check the :ref:`Fabric commands reference <fabric-commands>` to see a
comprehensive list of all Fabric commands available to deploy Pootle with a
detailed description for each command.
