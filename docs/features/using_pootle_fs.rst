.. _using_pootle_fs:

Using Pootle FS
===============

The task of Pootle FS is to keep the filesystem and Pootle in sync. There are
scenarios where items are not in sync and Pootle FS requires your intervention,
these are the commands you need to bring things back into sync and to resolve
conflicts.


.. _using_pootle_fs#background:

Pootle FS background
--------------------

To clarify the terminology that we use in Pootle FS:

- ``file`` - a translation file on disk
- ``store`` - a translation file in the Pootle database

Files and stores are usually associated and thus we are able to keep them
synchronised. But there might be files with no store (the store for a new file
has not yet been created in the Pootle database), and stores with no file (the
file has been removed from the filesystem).

Pootle FS works in these stages:

1. Actions are staged. An action is chosen to resolve each issue.
2. The system is synchronized. The staged action are actually performed.

Files that have never been synced are untracked, and thus they need to be
explicitly staged. Files previously synced are tracked, and thus automatically
staged if there are any changes. In the case of conflicts (changes both on disk
and in Pootle) it is also necessary to manually stage these to resolve which
version should prevail.

When staging it is possible to specify specific stores or files, or groups of
them using the ``-P`` and ``-p`` options. It is also possible to limit which
staged actions are executed by using these same options on the :djadmin:`sync`
command.


.. _using_pootle_fs#sync_tracked:

Syncing tracked stores or files
-------------------------------

When a store and its corresponding file are tracked and previously synced, then
they are automatically staged for syncing if either changes.

If both have changed then we will need to specify how to :ref:`resolve the
conflict <using_pootle_fs#resolve_conflicts>`.

To re-sync stores and files run:

.. code-block:: console

   (env) $ pootle fs sync MYPROJECT


.. _using_pootle_fs#add_files_stores:

Adding new files and stores
---------------------------

When new files appear on the filesystem that we want to bring into Pootle we
use :djadmin:`add`. And when new stores have appeared on Pootle that we want to
push to the filesystem we also use :djadmin:`add`:

.. code-block:: console
   
   (env) $ pootle fs add MYPROJECT
   (env) $ pootle fs sync MYPROJECT


Where :djadmin:`add` will stage the previously untracked files or stores.
While :djadmin:`sync` will synchronize, pulling the translations in the file
into the Pootle database or pushing translations from the stores in the
database to files on the filesystem.

Following this the file and store are now tracked.


.. _using_pootle_fs#remove_files_stores:

Removing files or stores
------------------------

A store or file can be missing from Pootle or the filesystem because it has
been removed, we use :djadmin:`rm` to remove such files and stores:

.. code-block:: console
   
   (env) $ pootle fs rm MYPROJECT
   (env) $ pootle fs sync MYPROJECT


This will remove the store or file, depending on whether it is the file or
store that remains.

Following this there is no such file or store on the filesystem or on Pootle.


.. _using_pootle_fs#resolve_conflicts:

Resolving conflicts
-------------------

Conflicts can occur if a tracked Pootle store and its corresponding file have
both changed. They can also arise if a new Pootle store is added and a matching
file has been added in the filesystem simultaneously.

There are four possible ways to resolve such conflicts:

1. Use the filesystem version and discard all Pootle translations
2. Use the Pootle version and ignore all filesystem translations
3. Merge translations and for unit conflicts choose Pootle's version and turn
   the filesystem version into a suggestion
4. Merge translations and for unit conflicts choose the filesystem version and
   turn the Pootle translation into a suggestion

The merge options are most useful where you need translators to resolve the
conflict.


.. _using_pootle_fs#resolve_conflict_overwrite_pootle:

Overwrite Pootle with filesystem version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You want to keep the version that is currently on the filesystem, discarding
all changes in Pootle:

.. code-block:: console
   
   (env) $ pootle fs resolve --overwrite --pootle-wins MYPROJECT
   (env) $ pootle fs sync MYPROJECT


.. _using_pootle_fs#resolve_conflict_overwrite_filesystem:

Overwrite filesystem with Pootle version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You wish to keep the version that is currently in Pootle, discarding all
changes in the filesystem:

.. code-block:: console
   
   (env) $ pootle fs resolve --overwrite MYPROJECT
   (env) $ pootle fs sync MYPROJECT


.. _using_pootle_fs#resolve_conflict_pootle_suggestion:

Use filesystem version and convert Pootle version into suggestion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To retain all translation and allow translators to resolve conflicts use
:djadmin:`resolve`. This will merge any non-conflicting units and convert
conflicts into suggestions, by default we use filesystem translations:

.. code-block:: console
   
   (env) $ pootle fs resolve MYPROJECT
   (env) $ pootle fs sync MYPROJECT


The result is that all non-conflicting units have been synchronised. For any
unit where both the store unit and file unit changed the translation is set to
the file unit translation with the store unit translation converted into a
suggestion. You can now review these suggestions to resolve the conflicts.


.. _using_pootle_fs#resolve_conflict_filesystem_suggestion:

Use Pootle version and convert filesystem version into suggestion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To retain all translation and allow translators to resolve conflicts use
:djadmin:`resolve`. This will merge any non-conflicting units and convert
conflicts into suggestions, the :option:`--pootle-wins <resolve --pootle-wins>`
option ensures that we use Pootle translations and convert filesystem
translations into suggestions:

.. code-block:: console
   
   (env) $ pootle fs resolve --pootle-wins MYPROJECT
   (env) $ pootle fs sync MYPROJECT
