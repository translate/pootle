.. _database-migration:

Database Migration
==================

.. note:: Please note that the database migration must be performed before
   upgrading Pootle.


Using :command:`dumpdata` and :command:`loaddata` commands to migrate between
databases is no longer supported.

The MySQL MyISAM backend is no longer supported. Use `InnoDB
<https://dev.mysql.com/doc/refman/5.6/en/innodb-storage-engine.html>`_ instead.

There are several tools available to migrate between databases. We recommend
having a look through this list for the following supported backends:

- `PostgreSQL <https://wiki.postgresql.org/wiki/Converting_from_other_Databases_to_PostgreSQL>`_
- `SQLite <https://www.sqlite.org/cvstrac/wiki?p=ConverterTools>`_
- `MySQL/MariaDB (InnoDB) <https://www.mysql.com/products/workbench/migrate/>`_
