.. _database-migration:

Database migration
==================

The default configuration for Pootle uses SQLite which is not really suited for
production use.  If you started using SQLite and want to migrate to another
database system such as :ref:`installation#mysql` or PostgreSQL without
recreating existing data, you can perform a database migration using the steps
described on this page.

.. note::

    A database migration is possible since Pootle 2.1.1 (or 2.0.6).  This
    migration will only work with Django 1.2 or later.

Quick summary
-------------

Two :doc:`manage.py commands <commands>` are needed::

    ./manage.py dumpdata -n > data.json

This saves all the content of the database as a JSON file::

    ./manage.py loaddata ./data.json

This reads all the data in the JSON file and creates the corresponding database
records.

Detailed migration process
--------------------------

The steps to migrate between databases are as follows:

  #. Make complete backups of all your files, settings and databases

  #. Ensure that you have at least Pootle 2.0.* or Pootle 2.1.*

  #. Don't change the version of Pootle at any stage during this process

  #. Ensure that you have at least Django 1.2.0

  #. Read about how to run :doc:`manage.py commands <commands>`

  #. Stop the Pootle server to avoid data changing while you migrate

  #. Leave current settings in tact and dump the data using the *dumpdata*
     command, note the ``-n`` option is required

  #. Create a new database for Pootle (:ref:`MySQL instructions
     <installation#mysql>`) and change *settings/90-local.conf* to point at this
     database

  #. Initialize the database using the ``./manage.py syncdb`` command

  #. Load the data using the *loaddata* command

  #. Restart the server; you should be running under the new database now

.. note::

    Pootle 2.1 and 2.2 database can be very large. Dumping and loading data
    will take long and will require lots of RAM. If you have a 2.0 install
    it is better to migrate the database first and then upgrade to 2.2, since
    the 2.0 database is relatively small.
