.. _pootle_fs_add_project:

Add a Pootle FS managed project
===============================

Pootle FS can work with different VCS systems as well as with the local file
system.

The following steps outline the setup of a Pootle FS based project:


Install Pootle FS plugins
-------------------------

.. note:: Pootle FS will work out of the box when synchronizing with the local
   file system. If this is the case you can safely skip this step.


Synchronizing against any version control system requires you add some
:ref:`additional packages and configuration <pootle_fs_install_plugins>`.


Create a project and set Pootle FS configuration for it
-------------------------------------------------------

Just follow the :ref:`Creating a project <project_setup#creating-the-project>`
instructions.

The **Path or URL** field must point to the translation files on Pootle's local
filesystem, e.g. ``/path/to/translations/MYPROJECT/``. You can use the
``{POOTLE_TRANSLATION_DIRECTORY}`` placeholder if you are using the ``localfs``
**Filesystem backend**, e.g. ``{POOTLE_TRANSLATION_DIRECTORY}MYPROJECT``
(``{POOTLE_TRANSLATION_DIRECTORY}`` will be transparently replaced by the value
of :setting:`POOTLE_TRANSLATION_DIRECTORY` setting).

The **Path mapping** field specifies the project layout using a glob like
``/path/to/translation/files/<language_code>/<dir_path>/<filename>.<ext>`` that
must start with ``/``, end with ``.<ext>``, and contain ``<language_code>``
(the rest of the placeholders are optional). Note you can easily fill this
field by selecting one of the available **Path mapping presets**.

If you are using the ``localfs`` **Filesystem backend** the **Path mapping**
will be combined with the specified **Path or URL**. For other backends it will
be relative to the root of the repository.

.. note:: If you are setting up Pootle FS for a VCS then configure as follows:

   - Set the **Filesystem backend** to the required VCS backend.
   - Set the **Path or URL** to point to the repository, e.g.
     ``git@github.com:user/repo.git``


If not all of your project's language codes match those available in Pootle,
then add language mapping configurations for those languages as explained in
the :ref:`Enable translation to a new language
<project_setup#initialize-new-tp>` instructions.


Connect Pootle FS with VCS repository
-------------------------------------

.. note:: You can safely skip this step if you are setting up the project to
   synchronize with the local file system.


- Create a SSH key:

  .. code-block:: console

    $ sudo -u USER-RUNNING-POOTLE ssh-keygen -b 4096

- Tell your upstream repo about the public key, allowing Pootle to be able to
  push to the repo.

  - In GitHub:

    - Either use the public key as a *Deploy key* for the repository on GitHub,
    - Or (**preferred**) add the public key to a GitHub user's *SSH and GPG
      Keys*. In most cases you want to create a specific Pootle GitHub user.


Pull the translations into Pootle
---------------------------------

Once the project is created and properly set up we can pull the translations
into Pootle:

.. code-block:: console

  (env) $ pootle fs state MYPROJECT
  (env) $ pootle fs add MYPROJECT
  (env) $ pootle fs sync MYPROJECT


Next steps
----------

Your project is now ready to use Pootle FS. In order to keep Pootle and the
filesystem or VCS synchronised you will need to learn how to :ref:`use Pootle
FS <using_pootle_fs>`.
