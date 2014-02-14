.. _fabric-deployment:

Automated deployment using Fabric
=================================

Pootle can be deployed using Fabric automation scripts. There are other methods
to deploy Pootle, but using Fabric with these scripts allows automated
deployments and simplifies maintenance tasks and the upgrade to newer versions.

The sample scripts bundled with Pootle allow you to deploy a Pootle server
using a Python virtualenv, running on a **Apache** server with *mod_wsgi* using
**MySQL** as database server on **Debian**-based systems. These sample scripts
can be modified to perform different deployments.

To see a comprehensive list of all Fabric commands available to deploy Pootle
check the :ref:`Fabric commands reference <fabric-commands>`.


.. _fabric-deployment#preparing-the-remote-server:

Preparing the remote server
---------------------------

Before performing an automated deployment using Fabric, make sure the
server where Pootle is going to be deployed has the required software.


.. _fabric-deployment#installing-required-software-on-the-remote-server:

Installing required software on the remote server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before proceeding, install the following software (if absent) on the
remote server:

- Python 2.5, 2.6, or 2.7
- `python-pip <http://www.pip-installer.org/>`_
- Git distributed version control system
- Apache web server
- MySQL database server
- OpenSSH server
- C compiler (to install Pootle's Python dependencies -- can be removed later)

.. note:: Currently only Debian-based (e.g. Ubuntu) servers are supported.

.. note:: If you have problems installing the dependencies during the bootstrap
   you are probably missing other packages needed to build those third-party
   Python modules. For example, `lxml <http://lxml.de/installation.html>`_
   needs development files for libxml2 and libxslt1 (as well as the C compiler
   mentioned above).

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

Before performing a deployment you will need to install some software on the
local computer and configure the necessary settings to connect to the remote
server.


.. _fabric-deployment#installing-required-software-on-the-local-computer:

Installing required software on the local computer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first step is to install the necessary software on the local computer.

.. note:: We strongly recommend using a virtual environment (virtualenv). Check
   the :ref:`Setting up the Environment <installation#setup_environment>` docs
   for information about virtualenvs.

.. code-block:: bash

    $ pip install Fabric


.. _fabric-deployment#getting-pootle-fabric-files:

Getting Pootle Fabric files
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pootle is bundled with sample scripts for deploying using Fabric. The relevant
files are:

- :file:`fabfile.py`
- Files inside the :file:`deploy/` directory

You can get those files from the `Pootle GitHub repository
<https://github.com/translate/pootle>`_. The rest of the Pootle files are not
necessary for this kind of deployment.


.. _fabric-deployment#setting-up-fabric:

Setting up Fabric
^^^^^^^^^^^^^^^^^

The :file:`deploy/` directory contains sample files that can be used in
combination with the :file:`fabfile.py` file for deploying Pootle servers.

There are two different deployment environments. Each one has a directory inside
:file:`deploy/`:

- Staging environment: :file:`deploy/staging/` directory
- Production environment: :file:`deploy/production/` directory

This way server administrators can separate their testing and real-world Pootle
servers.

For deploying a Pootle server using one of the environments it is necessary to
put some configuration files in place:

- :file:`deploy/pootle.wsgi` 
  WSGI script that will be used to run Pootle.

- :file:`deploy/ENVIRONMENT/fabric.py` 
  Module with settings that will be used in Fabric.

- :file:`deploy/ENVIRONMENT/settings.conf`
  Pootle-specific settings for the server (it will override the defaults). For
  example, the settings for connecting to the database will go here.

- :file:`deploy/ENVIRONMENT/virtualhost.conf`
  Apache VirtualHost configuration file.

In the previous paths ``ENVIRONMENT`` is the directory name for the chosen
environment (production or staging).

All the settings defined in the :file:`deploy/ENVIRONMENT/fabric.py` module
will populate the Fabric ``env`` dictionary, making the configuration keys
available in the :file:`deploy/ENVIRONMENT/settings.conf` and
:file:`deploy/ENVIRONMENT/virtualhost.conf` files. You can use basic Python
string formatting to access the configuration values.

.. note:: Sample configuration files are provided for reference under the
   :file:`deploy/` directory. Put them in the desired environment directory,
   and adapt them to your needs before running any Fabric commands.

Check :file:`pootle/settings/90-local.conf.sample` to see settings that you
might want to use in :file:`deploy/ENVIRONMENT/settings.conf`.

.. note:: If it is necessary you can adapt the :file:`deploy/pootle.wsgi` file
   to meet your needs.

Once you make your changes to the settings you are ready to run the
Fabric commands.

.. note:: For security, please make sure you change the ``db_password`` setting
   -- using the example one could make your server vulnerable to exploits.  The
   ``db_password`` setting is used both to properly configure Pootle, as well
   as to set up the database user access for the deployment.

   The ``db_root_password`` setting, on the other hand, is only used to
   configure the MySQL options file, if you choose to do this, and is only
   needed when creating the database (if the normal user does not have the
   necessary permissions).  Leaving this with default setting will have no
   security impact.


.. _fabric-deployment#how-to-run-fabric-commands:

How to run Fabric commands
--------------------------

In order to run Fabric commands for Pootle it is necessary that the directory
containing the :file:`fabfile.py` file and the ``deploy`` subdirectory be
included in the ``PYTHONPATH``.  If it is not, then add it using:

.. code-block:: bash

    $ export PYTHONPATH=`pwd`:$PYTHONPATH

The fabric commands need to know the type of environment in which
they are going to work, e.g. if the deployment will be for the production
environment. The Fabric commands for Pootle support two environments:
``production`` and ``staging``. To select the environment for running a
command just add it before the command like this:

.. code-block:: bash

    $ fab production bootstrap  # Use the 'production' environment
    $ fab staging bootstrap     # Or use the 'staging' environment

.. note:: It is necessary to :ref:`install Fabric 
   <fabric-deployment#installing-required-software-on-the-local-computer>` in
   order to be able to run the :command:`fab` command.


.. _fabric-deployment#provide-arguments:

Provide arguments
^^^^^^^^^^^^^^^^^

Some commands do accept arguments -- the argument name is followed by a colon
(:) and the value for the argument (with no spaces):

.. code-block:: bash

    $ fab production load_db:dumpfile=backup_mysql.sql  # Call load_db providing a database dump to load

The previous call runs the :ref:`load_db <fabric-commands#load-db>` command
providing the value ``backup_mysql.sql`` for its :option:`dumpfile` argument.


.. _fabric-deployment#tweak-the-environment:

Tweak the environment
^^^^^^^^^^^^^^^^^^^^^

One possible use for arguments is to tweak the environment when setting it,
before calling the commands:

.. code-block:: bash

    $ fab production:branch=stable/2.5.0 bootstrap  # Run bootstrap for a branch

In the previous example :ref:`bootstrap <fabric-commands#bootstrap>` is run
after setting the environment using :ref:`production
<fabric-commands#production>` but changing the branch to work on, to be the
value ``stable/2.5.0`` passed to the :option:`branch` argument.


.. _fabric-deployment#run-several-commands-in-a-row:

Run several commands in a row
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible to run several commands in a row with a single call:

.. code-block:: bash

    $ # Run several commands in a row using a single call to fab
    $ fab production:branch=stable/2.5.0 bootstrap create_db load_db:dumpfile=backup_mysql.sql

The previous call will run :ref:`production <fabric-commands#production>`
followed by :ref:`bootstrap <fabric-commands#bootstrap>`, :ref:`create_db
<fabric-commands#create-db>` and :ref:`load_db <fabric-commands#load-db>`, in
that exact order.

.. note:: If you want to know more about Fabric, please read `its documentation
   <http://docs.fabfile.org/en/latest/>`_.

See the :ref:`Fabric commands reference <fabric-commands>` for a
comprehensive list of all Fabric commands available for deploying Pootle,
with detailed descriptions of each command.


.. _fabric-deployment#configuring-passwordless-access:

Configuring passwordless access
-------------------------------

While it is not required, it is much easier to perform deployment operations
without interactive prompts for login, sudo, or MySQL database passwords:

* You can eliminate the need for an SSH login password by adding your public
  SSH key(s) to the :file:`~/.ssh/authorized_hosts` file of the user on the
  remote server.

* You can eliminate the need for sudo passwords by adding in the
  :file:`/etc/sudoers.d/` directory on the remote server, a file (with
  permissions mode ``440``) containing the line:

  ::

     username ALL = (ALL) NOPASSWD: ALL

  where *username* must be replaced with the user configured in the
  :file:`fabric.py` settings file.

* You can eliminate the need for MySQL passwords by configuring the database
  password(s) in the :file:`fabric.py` settings file, running the
  :ref:`mysql_conf <fabric-commands#mysql-conf>` fabric command to create a
  MySQL options file for the remote user:

  .. code-block:: bash

      $ fab production mysql_conf  # Set up MySQL options file

  and then modifying the :file:`fabric.py` settings file to un-comment the
  alternate value for :setting:`db_password_opt` (and optionally
  :setting:`db_root_password_opt`, if :setting:`db_root_password` is
  configured).


.. _fabric-deployment#typical-usage-example:

Typical Usage Example
---------------------

A typical usage example is included here in order to provide a more easy to
understand example on how to use this deployment method and the available
commands.


.. _fabric-deployment#bootstrap-environment:

Bootstrapping the environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can install the Pootle software, configuration files, and directory tree(s)
with the bootstrap command.

.. code-block:: bash

    $ export PYTHONPATH=`pwd`:$PYTHONPATH
    $ fab production:branch=stable/2.5.0 bootstrap  # Install Pootle 2.5


.. _fabric-deployment#setting-up-the-database:

Setting Up the Database
^^^^^^^^^^^^^^^^^^^^^^^

When setting up the database there are several possible scenarios:

* If creating a new database from scratch:

  .. code-block:: bash

      $ fab production create_db  # Creates Pootle DB on MySQL
      $ fab production update_config  # Uploads the settings
      $ fab production setup  # Creates the DB tables and populates the DB

* If creating a blank database and populating with a (local) database backup:

  .. code-block:: bash

      $ fab production create_db  # Creates Pootle DB on MySQL
      $ fab production load_db:dumpfile=backup_mysql.sql # Populate DB from local dump

  .. note:: The :option:`dumpfile` (for :ref:`load_db
     <fabric-commands#load-db>` and :ref:`dump_db <fabric-commands#dump-db>`)
     is local to the system where Fabric runs, and is automatically copied
     to/from the remote server.

* If updating a previous version database (possibly just loaded with
  :ref:`load_db <fabric-commands#load-db>`) to the latest version of the
  schema:

  .. code-block:: bash

      $ fab production update_config  # Uploads the settings
      $ fab production setup  # Updates the DB to the latest version


.. _fabric-deployment#enabling-the-web-server:

Enabling the web server
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    $ fab production:branch=stable/2.5.0 deploy
