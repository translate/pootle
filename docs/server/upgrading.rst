.. _upgrading:

Upgrading
=========

Here are some points to take into account while performing Pootle
upgrades.


.. _upgrading#checklist:

Checklist
---------

Before upgrading Pootle to a newer version, make sure to go through this
checklist.

* Familiarize yourself with :doc:`important changes </changelog>` in
  Pootle over the versions.

* If you want to change databases, which might be needed when upgrading from
  Pootle 1.x to Pootle 2.x, or from Pootle 2.0.x to 2.1.x, then have a look at
  the :doc:`database migration <database_migration>` page first, although some
  of the issues on this page could still be relevant.

* Check the :doc:`installation <installation>` instructions for the newer
  version, and ensure that you have all the dependencies for the newer version.

* Always make backups of all your translation files (your whole
  :setting:`PODIRECTORY`) and your custom settings file. You can synchronize
  all your translation files with the database using the :ref:`sync_stores
  <commands#sync_stores>` command before you make your backups.

* Make a backup of your complete database using the appropriate *dump*
  command for your database system. For example :command:`mysqldump` for MySQL,
  or :command:`pg_dump` for PostgreSQL.

* If you are upgrading from a version of Pootle that uses *localsettings.py*
  then you want to make sure your configuration file is read when Pootle
  starts. For more information, read about :ref:`customizing settings
  <settings#customizing>`.

* You might want to look for any new :ref:`available settings
  <settings#available>` in the new version that you might want to
  configure.

* After a successful upgrade, consider clearing your cache. For users of
  memcached it is enough to restart memcached. For users of the default
  database cache, you can drop the `pootlecache` table and recreate it
  with:

  .. code-block:: bash

    $ pootle createcachetable pootlecache

* Finally run the :ref:`collectstatic <commands#collectstatic>` and
  :ref:`assets build <commands#assets>` commands.


.. _upgrading#database:

Performing the Database Upgrade
-------------------------------

.. versionchanged:: 2.5.1

Once you have the new code configured to in your server using the correct
settings file, you will be ready to run the database schema and data
upgrade procedure.

.. warning::

  Always make database backups before running any upgrades.

.. note::

  If you are upgrading from a Pootle version older than 2.5, you will need
  an extra step at the beginning: use the :ref:`updatedb command
  <commands#updatedb>` first to upgrade the database schema to the state
  of Pootle 2.5.

  This is necessary due to the changes made to the schema migration
  mechanisms after the 2.5 release.


In the first step, the syncdb command will create any missing database
tables that don't require any migrations.

.. code-block:: bash

  $ pootle syncdb --noinput


.. note::

  At this point in time, and due to Pootle's transitioning to South, you will
  need to run a fake migration action in order to let South know which is your
  current database schema.

  You can execute the fake migration by running the following:

  .. code-block:: bash

    $ pootle migrate --all --fake 0001

The next step will perform any pending schema migrations. You can read more
about the :ref:`migrate command <south:commands>` in South's documentation.

.. code-block:: bash

  $ pootle migrate

Lastly, the :ref:`upgrade command <commands#upgrade>` will perform any extra
operations needed by Pootle to finish the upgrade and will record the current
code build versions for Pootle and the Translate Toolkit.

.. code-block:: bash

  $ pootle upgrade


.. _upgrading#custom_changes:

Custom Changes
--------------

If you made any changes to Pootle code, templates or styling, you will want to 
ensure that your upgraded Pootle contains those changes.  How hard that is will
depend entirely on the details of these changes.

Changes made to the base template are likely to work fine, but changes to
details will need individual inspection to see if they can apply
cleanly or have to be reimplemented on the new version of Pootle.

Since Pootle 2.5 :doc:`customization of style sheets and templates
</developers/customization>` have become much easier to seperate from the
standard code.  If you are migrating to Pootle 2.5+ then use this opportunity
to move your code to the correct customization locations.
