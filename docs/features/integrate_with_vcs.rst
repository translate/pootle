.. _integrate_with_vcs:

Integrate with version control system
=====================================

.. note:: Pootle FS will work out of the box when synchronizing with the local
   file system. If this is the case you can safely skip the integration with
   version control.


If the translations for your project are stored in a version control system
(VCS in short), then might be a good idea to directly integrate with the VCS.
The following instructions work either if you project is already setup to use
the ``localfs`` Pootle FS backend, or if you are creating and setting a new
project to directly work with the VCS.


.. _integrate_with_vcs#install-vcs-plugins:

Install Pootle FS plugins for VCS
---------------------------------

Pootle FS provides support for different VCS systems through plugins, so in
order for Pootle to work with a specific VCS it is necessary to install its
plugin. For example for Git:

- Install the plugin:

  .. highlight:: console
  .. parsed-literal::

    (env) $ pip install --pre Pootle[git]


- Add the plugin to :setting:`INSTALLED_APPS` in your custom Pootle settings:

  .. code-block:: python

    INSTALLED_APPS += ['pootle_fs_git']


This is done once for the whole Pootle server.


.. _integrate_with_vcs#connect-with-vcs:

Connect Pootle FS with VCS repository
-------------------------------------

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


.. _integrate_with_vcs#configure-project-to-use-vcs:

Configure the project to use VCS
--------------------------------

After installing the necessary Pootle FS plugin and connecting Pootle FS with
the VCS repository, it is now necessary to alter the project configuration:

- Deactivate any existing automatic synchronization (like :command:`cron`
  entries).
- Disable the project to prevent changes from translators.
- Ensure you have synchronized all the translation files to disk.
- Ensure you have committed all the translation files to your version control
  system.
- Set the project's **Filesystem backend** to the appropriate VCS backend.
- Set the URL to your version control repository in the project's **Path or
  URL**, e.g. ``git@github.com:user/repo.git``.
- Synchronize as follows:

  .. code-block:: console

    (env) $ pootle fs fetch $MYPROJECT
    (env) $ pootle fs sync $MYPROJECT

- Enable the project again.
- Enable automatic synchronization again.


Your project is now ready to synchronize with the configured repository using
Pootle FS. You might want to learn more about how to :ref:`use Pootle FS
<using_pootle_fs>`.
