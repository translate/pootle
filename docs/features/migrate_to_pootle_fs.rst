.. _migrate_to_pootle_fs:

Migrating to Pootle FS
======================

When upgrading Pootle your projects will be automatically migrated to use the
Pootle FS ``localfs`` backend.

.. note:: Before continuing :ref:`ensure all projects were properly migrated
   to Pootle FS <upgrading#check-pootle-fs-migration>` when upgrading Pootle.


While Pootle will continue to support :djadmin:`update_stores` and
:djadmin:`sync_stores` these are now deprecated, so it is advisable you start
to adjust your workflow to use Pootle FS.


.. _migrate_to_pootle_fs#adjust-existing-automation:

Adjust existing automation
--------------------------

If you have scripts using :djadmin:`sync_stores` and :djadmin:`update_stores`
then you might want to continue using those until you can migrate them to
Pootle FS commands.

:djadmin:`sync_stores` and :djadmin:`update_stores` make use of Pootle FS
infrastructure so they are in fact still using Pootle FS.  The difference is
that they mimic the monodirectional behaviour of the old commands.  Pootle FS
will synchronise in both directions at a unit level, while
:djadmin:`update_stores` will only load new and changed units and
:djadmin:`sync_stores` will only synchronise Pootle changes to disk.

The advantage of this monodirectional mode is that you can add scripts to adapt
files after synchronising or before loading into Pootle.  Your scripts changing
files on disk will likely mess with direct Pootle FS change detection.

You may want to look at the format adapters for future massaging or formats.


.. _migrate_to_pootle_fs#replacing-update_stores-and-sync_stores:

Replacing update_stores and sync_stores
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:djadmin:`update_stores` can be replaced with the following set of Pootle FS
commands:

.. code-block:: console

    (env) $ pootle fs fetch my-project
    (env) $ pootle fs resolve my-project --overwrite
    (env) $ pootle fs sync my-project --update=pootle


.. note:: To narrow down the execution to a particular language in a project
   you must append the ``--fs-path`` argument for each of command in the
   previous snippet. For example ``--fs-path=my-project/fr/*`` constrains to
   the project's French filesystem files.


:djadmin:`sync_stores` can be replaced with the following set of Pootle FS
commands:

.. code-block:: console

    (env) $ pootle fs fetch my-project
    (env) $ pootle fs resolve my-project --overwrite --pootle-wins
    (env) $ pootle fs sync my-project --update=fs


.. note:: To narrow down the execution to a particular language in a project
   you must append the ``--pootle-path`` argument for each of command in the
   previous snippet. For example ``--pootle-path=/de/my-project/*`` constrains
   to the project's German database stores.
