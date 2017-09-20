.. _pootle_fs_add_project:

Add a Pootle FS managed project
===============================

Pootle FS can work with different VCS systems as well as with the local file
system.

The following steps outline the setup of a Pootle FS based project:


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
