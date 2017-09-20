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

You may want to look at the format adaptors for future massaging or formats.


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


.. _migrate_to_pootle_fs#integrating-with-vcs:

Integrating with version control
--------------------------------

.. note:: Pootle FS will work out of the box when synchronizing with the local
   file system. If this is the case you can safely skip the integration with
   version control.


With files moved to ``localfs`` it might be a good time to consider directly
integrating with version control.


.. _migrate_to_pootle_fs#install-vcs-plugins:

Install Pootle FS plugins for VCS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pootle FS provides support for different VCS systems through plugins, so in
order for Pootle to work with a specific VCS it is necessary to install its
plugin.  For examples for Git:

- Install the plugin:

  .. highlight:: console
  .. parsed-literal::

    (env) $ pip install |--process-dependency-links --pre| Pootle[git]


- Add the plugin to :setting:`INSTALLED_APPS`:

  .. code-block:: python

    INSTALLED_APPS += ['pootle_fs_git']


This is done once for the whole Pootle server.


.. _migrate_to_pootle_fs#connect-with-vcs:

Connect Pootle FS with VCS repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The version control system also must provide access for Pootle FS to
synchronize:

- Create a SSH key:

  .. code-block:: console

    $ sudo -u USER-RUNNING-POOTLE ssh-keygen -b 4096

- Tell your upstream repository about the public key, allowing Pootle to be
  able to push to the repository. For example for GitHub:

  - Either use the public key as a **Deploy key** for the repository on GitHub,
  - Or (**preferred**) add the public key to a GitHub user's **SSH and GPG
    Keys**. In most cases you want to create a specific user in GitHub for
    Pootle.


.. _migrate_to_pootle_fs#configure-project-to-use-vcs:

Configure the project to use VCS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After installing the necessary Pootle FS plugin and connecting Pootle FS with
the VCS repository, it is now necessary to alter the project configuration:

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
