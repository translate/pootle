.. _database-migration:

Database Migration
==================

The default configuration for Pootle uses SQLite which is not really suited for
production use. If you started using SQLite and want to migrate to another
database system such as MySQL or PostgreSQL without recreating existing data,
you can perform a database migration using the steps described on this page.

.. note::

    A database migration is possible since Pootle 2.1.1. It is possible to do
    the database migration using the version 2.0.6, which was specifically
    added to allow database migration. This migration will only work with
    Django 1.2 or later.


.. _database-migration#detailed-migration-process:

Detailed Migration Process
--------------------------

.. note::

    Pootle 2.1.x and 2.5.x database can be very large. Dumping and loading data
    will take long and will require lots of RAM. If you have a 2.0 install it
    is better to migrate the database first and then upgrade to 2.5, since the
    2.0 database is relatively small.

The steps to migrate between databases are as follows:

#. Make **complete backups** of all your files, settings and databases.

#. Ensure that you have:

   #. At least Pootle 2.0.* or Pootle 2.1.*.

   #. At least Django 1.2.0.

#. Don't change the version of Pootle at any stage during this process.

#. Read about how to run :doc:`management commands <commands>`.

#. Stop the Pootle server to avoid data changing while you migrate.

#. Leave current settings intact.

#. Dump the data to a JSON file using the :command:`dumpdata` command. Note the
   :option:`-n` option.

   .. code-block:: bash

        $ pootle dumpdata -n > data.json

#. Create a new database for Pootle.

#. Change :ref:`your settings <settings>` to point at this new database.

#. Initialize the new database using the :command:`syncdb` command.

   .. note::

        Sometimes not removing records introduced by :command:`syncdb` can
        create problems. So if you experience any failure during
        :command:`loaddata` execution that can't be solved by any other mean,
        then remove all the records from the new database while keeping the
        tables intact.

#. Load the data from the JSON file in the new database using the
   :command:`loaddata` command:

   .. code-block:: bash

        $ pootle loaddata ./data.json

   .. note::

        If you experience any problem during :command:`loaddata` execution, you
        may find it helps to instead export the data with:

        .. code-block:: bash

            $ pootle dumpdata > data.json

        avoiding the use of :option:`-n` or :option:`--natural` options.

#. Restart the server; you should be running under the new database now.


.. note::

    Some other problems reported during database migration may be solved by
    commenting all signal calls in Pootle code during the database migration
    process. If you do so, remember to uncomment them after the migration.
