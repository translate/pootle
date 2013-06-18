.. _fabric-commands:

Available Fabric commands
=========================

.. versionadded:: 2.5

   Starting in this release, Pootle includes Fabric deployment scripts.

The sample Fabric scripts provide several commands that you can use to easily
deploy your Pootle site.

.. note:: Most of the examples in this section will use the ``production``
   environment, but remember that other environments can be used as well.


.. _fabric-commands#bootstrap:

bootstrap
---------

This command:

- Creates the required directories, asking to remove them first if they already
  exist
- Creates a virtual environment (virtualenv) and activates it
- Clones the Pootle repository from GitHub
- Checks out the specified branch, using master if no branch is specified
- Installs the deployment requirements as listed in :file:`requirements/`,
  including the base requirements as well

.. note:: While running it may ask for the remote server ``root`` password,
   or more likely the ``sudo`` password, which is the standard password for the
   remote user configured in the environment.

.. note::
   .. versionchanged:: 2.5.1 Added support for bootstrapping from a given
      branch on Pootle repository.

Available options:

``branch``
  A specific branch to check out in the repository.

  Default: ``master``.

Examples:

.. code-block:: bash

    $ fab production bootstrap  # Call that will use the default 'master' branch
    $ fab production bootstrap:branch=stable/2.5.0  # Call which provides a branch


.. _fabric-commands#compile-translations:

compile_translations
--------------------

This command:

- Compiles the MO files for Pootle translations

Examples:

.. code-block:: bash

    $ fab production compile_translations


.. _fabric-commands#create-db:

create_db
---------

.. versionadded:: 2.5.1

This command:

- Creates a new blank database using the settings provided to Fabric in the
  chosen environment

.. note:: While running it may ask for the remote server ``root`` password or
   the ``sudo`` password (standard password for the remote user configured in
   the environment) as well as the specified ``db_user`` and/or database root
   password.  See the :ref:`mysql_conf <fabric-commands#mysql-conf>` command
   for a way to eliminate the need for database password prompting.

.. note:: This command will try to create a database on MySQL, which will fail
   if MySQL is not installed or the settings don't provide configuration data
   for creating the database.

Examples:

.. code-block:: bash

    $ fab production create_db


.. _fabric-commands#deploy:

deploy
------

This command:

- Calls the :ref:`update_code <fabric-commands#update-code>` command providing
  the specified branch, if any
- Calls the :ref:`deploy_static <fabric-commands#deploy-static>` command
- Calls the :ref:`install_site <fabric-commands#install-site>` command

.. note:: While running it may ask for the remote server ``root`` password or
   the ``sudo`` password (standard password for the remote user configured in
   the environment).

.. note::
   .. versionchanged:: 2.5.1 Added support for deploying from a given branch
      on Pootle repository.

Available options:

``branch``
  A specific branch to check out in the repository.

  Default: ``master``.

Examples:

.. code-block:: bash

    $ fab production deploy  # Call that will use the default 'master' branch
    $ fab production deploy:branch=stable/2.5.0  # Call which provides a branch


.. _fabric-commands#deploy-static:

deploy_static
-------------

This command:

- Creates :file:`pootle/assets/` directory if it does not exist
- Runs :ref:`collectstatic --noinput --clear <commands#collectstatic>` to
  collect the static files
- Runs :ref:`assets build <commands#assets>` to create the assets

Examples:

.. code-block:: bash

    $ fab production deploy_static


.. _fabric-commands#disable-site:

disable_site
------------

This command:

- Disables the Pootle site on Apache using the Apache :command:`a2dissite`
  command

.. note:: While running it may ask for the remote server ``root`` password or
   the ``sudo`` password (standard password for the remote user configured in
   the environment).

Examples:

.. code-block:: bash

    $ fab production disable_site


.. _fabric-commands#dump-db:

dump_db
-------

.. versionadded:: 2.5.1

This command:

- Dumps the database to the provided filename using the :command:`mysqldump`
  command
- Downloads the dumpfile to the local computer

.. note:: While running it may ask for the remote server ``root`` password or
   the ``sudo`` password (standard password for the remote user configured in
   the environment) as well as the specified ``db_user`` and/or database root
   password.  See the :ref:`mysql_conf <fabric-commands#mysql-conf>` command
   for a way to eliminate the need for database password prompting.

.. note:: This commands can be used to perform periodic backups, that can be
   imported later using the :ref:`load_db <fabric-commands#load-db>`
   command.

Available options:

``dumpfile``
  The filename for the file where the database will be dumped.

  Default: ``pootle_DB_backup.sql``.

Examples:

.. code-block:: bash

    $ fab production dump_db  # Call that will use the default filename
    $ fab production dump_db:dumpfile=backup_mysql.sql  # Call which provides a filename


.. _fabric-commands#enable-site:

enable_site
-----------

This command:

- Enables the Pootle site on Apache using the Apache :command:`a2ensite`
  command

.. note:: While running it may ask for the remote server ``root`` password or
   the ``sudo`` password (standard password for the remote user configured in
   the environment).

Examples:

.. code-block:: bash

    $ fab production enable_site


.. _fabric-commands#initdb:

initdb
------

.. versionadded:: 2.5.1

This command:

- Runs :ref:`initdb <commands#initdb>` to initialize the database

Examples:

.. code-block:: bash

    $ fab production initdb


.. _fabric-commands#install-site:

install_site
------------

This command:

- Calls the :ref:`update_config <fabric-commands#update-config>` command
- Calls the :ref:`enable_site <fabric-commands#enable-site>` command

.. note:: While running it may ask for the remote server ``root`` password or
   the ``sudo`` password (standard password for the remote user configured in
   the environment).

Examples:

.. code-block:: bash

    $ fab production install_site


.. _fabric-commands#load-db:

load_db
-------

.. versionadded:: 2.5.1

This command:

- Uploads the given SQL dump file to the remote server
- Imports it to the database specified on Fabric settings using the
  :command:`mysql` command

.. note:: While running it may ask for the remote server ``root`` password or
   the ``sudo`` password (standard password for the remote user configured in
   the environment) as well as the specified ``db_user`` and/or database root
   password.  See the :ref:`mysql_conf <fabric-commands#mysql-conf>` command
   for a way to eliminate the need for database password prompting.

.. note:: You must first create the database you will import (e.g. using the
   :ref:`create_db <fabric-commands#create-db>` command) before calling this
   command,

Available options:

``dumpfile``
  The SQL dump filename that will be uploaded to and imported into an existing
  database on the remote server. This file can be created using the
  :ref:`dump_db <fabric-commands#dump-db>` command.

  .. note:: This is a required option.

Examples:

.. code-block:: bash

    $ fab production create_db  # Remember to create the DB first
    $ fab production load_db:dumpfile=backup_mysql.sql


.. _fabric-commands#migratedb:

migratedb
---------

.. versionadded:: 2.5.1

This command:

- Runs :ref:`migrate <commands#migrate>` to update the 2.5 or later database
  schema to the latest version

Examples:

.. code-block:: bash

    $ fab production migratedb


.. _fabric-commands#mysql-conf:

mysql_conf
----------

.. versionadded:: 2.5.1

This command creates a :file:`.my.cnf` MySQL options file on the remote system
with the password(s) for database access stored in them (the passwords are
taken from the :file:`fabric.py` settings file).  Once you have done this, you
can un-comment the alternate ``db_password_opt`` and ``db_root_password_opt``
settings in :file:`fabric.py`, which will eliminate the need for password
prompting on all MySQL operations.

Examples:

.. code-block:: bash

    $ fab production mysql_conf


.. _fabric-commands#production:

production
----------

This command:

- Sets up the configuration for the ``production`` environment in Fabric
  settings

.. note:: This commands is useless unless it is called before another command or
   commands.

Examples:

.. code-block:: bash

    $ fab production bootstrap

In the previous example :command:`production` is called to set up the
environment for calling :command:`bootstrap` afterwards.


.. _fabric-commands#setup-db:

setup_db
--------

.. versionadded:: 2.5.1

This command:

- Runs :ref:`syncdb --noinput <commands#syncdb>` to create the database schema
- Runs :ref:`initdb <commands#initdb>` to populate the standard schema objects
- Runs :ref:`migrate <commands#migrate>` to bring the database schema
  up to the latest version

Examples:

.. code-block:: bash

    $ fab production setup_db


.. _fabric-commands#staging:

staging
-------

This command:

- Sets up the configuration for the ``staging`` environment in Fabric settings

.. note:: This commands is useless unless it is called before another command or
   commands.

Examples:

.. code-block:: bash

    $ fab staging bootstrap

In the previous example :command:`staging` is called to set up the environment
for calling :command:`bootstrap` afterwards.


.. _fabric-commands#syncdb:

syncdb
------

.. versionadded:: 2.5.1

This command:

- Runs :ref:`syncdb --noinput <commands#syncdb>` to create the database schema

Examples:

.. code-block:: bash

    $ fab production syncdb


.. _fabric-commands#touch:

touch
-----

This command:

- Reloads daemon processes by touching the WSGI file

Examples:

.. code-block:: bash

    $ fab production touch


.. _fabric-commands#update-code:

update_code
-----------

This command:

- Updates the Pootle repository from GitHub
- Checks out the specified branch, using master if no branch is specified
- Updates the deployment requirements as listed in :file:`requirements/`,
  including the base requirements as well

.. note::
   .. versionchanged:: 2.5.1 Added support for updating code from a given branch
      on Pootle repository.

Available options:

``branch``
  A specific branch to check out in the repository.

  Default: ``master``.

Examples:

.. code-block:: bash

    $ fab production update_code


.. _fabric-commands#update-config:

update_config
-------------

This command:

- Will upload the configuration files included in the chosen environment to the
  remote server:

  - Configure VirtualHost using the provided :file:`virtualhost.conf`
  - Configure WSGI application using the provided :file:`pootle.wsgi`
  - Configure and install custom settings for Pootle using the provided
    :file:`settings.conf`

.. note:: While running it may ask for the remote server ``root`` password or
   the ``sudo`` password (standard password for the remote user configured in
   the environment).

Examples:

.. code-block:: bash

    $ fab production update_config


.. _fabric-commands#update-db:

update_db
---------

This command:

- Runs :ref:`updatedb <commands#updatedb>` and :ref:`migrate
  <commands#migrate>` to update the database schema to the latest version

Examples:

.. code-block:: bash

    $ fab production update_db
