.. _migrate_to_pootle_fs:

Migrating to Pootle FS
======================

While Pootle will continue to support :djadmin:`update_stores` and
:djadmin:`sync_stores` these are now deprecated.

When upgrading Pootle your projects will be automatically migrated to use the
Pootle FS ``localfs`` backend.


Post migration check
--------------------

Once the Pootle migration is complete you need to check that all items where
migrated correctly:

.. code-block:: console

   (env) $ pootle fs
   (env) $ pootle fs state MYPROJECT


The first lists all the available Pootle FS projects, the second command will
show the state of tracked files.

Ideally we want the state to show no results, i.e. that all files on disk and
in Pootle are in sync and are being tracked.  If the migration to Pootle FS was
not able to fully understand your layout then there may be untracked files.

If there are untracked files you will want do some of these steps:

1. ``fs add`` or ``fs rm`` any files that should be tracked but are currently
   untracked.
2. Moving and renaming files on the filesystem could resolve missing files.
3. Adding language mappings could correctly map FS and Pootle stores.


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

You may want to look at the format adaptors for future massaging or formats.


.. _migrate_to_pootle_fs#migrating-to-vcs:

Migrating to version control
----------------------------

With files moved to ``localfs`` it might be a good time to consider directly
integrating with version control.

1. Make sure you have installed the needed Pootle FS :ref:`plugin for the
   version control backend <pootle_fs_install_plugins>` you are using.
2. (optional but recommended) Disable the project.
3. Ensure you have synchronized all your files and committed them to your
   version control system.
4. Instead of ``localfs``, set the backend appropriately.
5. Set the URL to your version control repository.
6. Synchronize as follows:

   .. code-block:: console

     (env) $ pootle fs fetch --force MYPROJECT
     (env) $ pootle fs sync MYPROJECT
