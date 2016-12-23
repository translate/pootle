.. _pootle_fs_install_plugins:

Install Pootle FS plugins for VCS
=================================

To work with VCS systems Pootle FS requires some additional packages and
configuration.


Install the Pootle FS plugins
-----------------------------

Pootle FS provides support for different VCS systems through plugins, so in
order to work with a specific VCS it is necessary to install its plugin.  For
examples for Git:

- Install the plugin:

  .. highlight:: console
  .. parsed-literal::

    (env) $ pip install |--process-dependency-links --pre| Pootle[git]


- Add the plugin to :setting:`INSTALLED_APPS`:

  .. code-block:: python

    INSTALLED_APPS += ['pootle_fs_git']


This is done once for the whole Pootle server.


Next steps
----------

Your project is now ready to use Pootle FS with the chosen VCS systems, you can
now proceed to :ref:`add a Pootle FS managed project <pootle_fs_add_project>`.
