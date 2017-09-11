.. _pootle_fs:

Pootle FS
=========

Pootle FS is Pootle's integration with version control plugin systems. It
allows Pootle to synchronize with an external repository containing your
translations, keep them synchronised and manage and resolve any conflicts
either automatically or via user input.


Aims
----

* Allow Pootle data to be stored on version control systems
* Abstract version control systems into a standard method across all systems
* Ensure that we don't lose any data
* Ensure that changes made on Pootle and the filesystem can seamlessly move
  from one to the other


Core concepts
-------------

Stores and files
  Pootle contains stores of translation units. The filesystem contains files.

Tracked and untracked
  When a store is associated with a file, it is tracked, if it is not
  yet associated then it is untracked. And vice versa.

States
  Tracked and untracked files and stores will be in various states depending on
  a number of things. Have they just appeared, have they changed, have they
  been removed, etc.

Actions
  Based on the states we can determine what actions might be applicable to
  the stores and files.

Staging
  We use Pootle FS commands to stage an action. Staging is not execution of
  those actions but merely preparing these actions for execution.

Synchronisation
  This is the act of executing the staged actions.


Understanding operations
------------------------

At any time we are able to query the state of Pootle FS using :djadmin:`fs
state <state>` command. The results of this operation will indicate if there
are any actions you need to specify to resolve any conflicts or if there are
untracked files.

You specify *Actions* that need to be taken to resolve conflicts or to ensure
that files are tracked. This could be adding a file, removing a file or merging
conflicting translations. This is the process of staging actions.

The final step is to synchronise Pootle and your filesystem. This operation
takes your staged actions and executes them.


What is a filesystem
--------------------

A filesystem is actually itself a Pootle FS plugin. Currently two exist:

1. **localfs** - allowing synchronization with the filesystem on which Pootle
   is running
2. **git** - synchronization with a Git repository


You can write a plugin for any version control system, Pootle FS will ensure
that the same commands and operations are used to ensure Pootle and your
filesystem stay synchronized.


How does Pootle FS relate to update_stores/sync_stores
------------------------------------------------------

.. note:: Read this if you have used previous versions of Pootle.


Previous versions of Pootle made use of two commands, :djadmin:`update_stores`
and :djadmin:`sync_stores`, to allow translations to be pushed into Pootle or
pulled from Pootle.

These two commands still exist but we will be phasing these out in the long
term to make everything use Pootle FS.

You can find an outline of how to use Pootle FS on your existing Pootle
projects in the :ref:`adding a Pootle FS managed project
<pootle_fs_add_project>` instructions.

Once you are familiar with Pootle FS you can start :ref:`migrating your
projects to Pootle FS <migrate_to_pootle_fs>`.
