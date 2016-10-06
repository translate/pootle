.. _migrate_to_pootle_fs:

Migrating to Pootle FS
======================

While Pootle will continue to support :djadmin:`update_stores` and
:djadmin:`sync_stores` this will eventually be deprecated. Thus it makes sense
to migrate your projects to Pootle FS.

These steps will convert a project currently hosted in
:setting:`POOTLE_TRANSLATION_DIRECTORY` into a Pootle FS ``localfs`` project.


Preparation
-----------

1. (optional) Disable the project to prevent translators working on the stores.
   You can also, quite safely, perform the migration live.
2. Run :djadmin:`sync_stores` to ensure that all translations in Pootle are on
   the filesystem. The filesystem and Pootle should now have exactly the same
   data.

   .. code:: console

      (env) $ pootle sync_stores --project=MYPROJECT


Setup Pootle FS
---------------

1. In the Project Admin interface, change the *Project Tree Style* to
   ``Allow Pootle FS to manage filesystems``.

   .. image:: ../_static/set_project_pootle_fs.png

2. Click on the ``Filesystems`` link below the project edit form and set the
   following:

   .. image:: ../_static/pootle_fs_link.png

   * *Filesystem backend* to ``localfs``
   * *Backend URL or path* to the value of
     :setting:`POOTLE_TRANSLATION_DIRECTORY` + MYPROJECT, e.g.
     :file:`/path/to/pootle/translations/MYPROJECT`


First synchronization
---------------------

Now that our project is setup we can initiate the first synchronization to
ensure all files are tracked:

.. code:: console

   (env) $ pootle fs add --force MYPROJECT
   (env) $ pootle fs sync MYPROJECT


This will use translations from Pootle and ignore those on the filesystem.


Variations on the theme
-----------------------

The process above outlines how you can move an ``update_stores`` project to
Pootle FS on the local filesystem with Pootle winning. You might want to do
some other things such as:


Filesystem wins
^^^^^^^^^^^^^^^

The :djadmin:`sync_stores` in our recipe above ensures that everything is in
sync. However if you have scripts that commit and update files you might prefer
to let the filesystem win in which case rather use:

.. code:: console

   (env) $ pootle fs fetch --force MYPROJECT


Migrating to version control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Make sure you have installed the needed Pootle FS plugin for the version
   control backend you are using.
2. (optional but recommended) Disable the project.
3. Ensure you have synchronized all your files and committed them to your
   version control system.
4. Instead of ``localfs``, set the backend appropriately.
5. Set the URL to your version control repository.
6. Synchronize as follows:

   .. code:: console

     (env) $ pootle fs fetch --force MYPROJECT
     (env) $ pootle fs sync MYPROJECT
