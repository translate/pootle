.. _pootle_fs_install_plugins:

Install Pootle FS plugins for VCS
=================================

To work with VCS systems Pootle FS requires some additional packages and
configuration.


Install the Pootle FS plugins
-----------------------------

Pootle FS provides support for different VCS systems through plugins, so in
order to work with a specific VCS it is necessary to install its plugin:

- In :file:`requirements/_pootle_fs.txt` uncomment the lines for the required
  VCS plugins that you want to enable.
- Run the following command:

  .. code-block:: console

    (env) $ pip install -r requirements/_pootle_fs.txt


- In your settings add the plugin apps to ``INSTALLED_APPS``, e.g. for ``git``:

  .. code-block:: python

    INSTALLED_APPS += ['pootle_fs_git']


This is done once for the whole Pootle server.


Next steps
----------

Your project is now ready to use Pootle FS with the chosen VCS systems, you can
now proceed to :ref:`add a Pootle FS managed project <pootle_fs_add_project>`.
