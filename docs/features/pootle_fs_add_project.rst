.. _pootle_fs_add_project:

Add a Pootle FS managed project
===============================

Pootle FS can work with different VCS systems as well as with the local file
system.


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
