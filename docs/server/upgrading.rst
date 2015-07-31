.. _upgrading:

Upgrading
=========

These are the instructions for upgrading Pootle from an older version to a new
release.

.. warning::

  When upgrading please ensure that you:

  - **Carefully read this page** before proceeding
  - Make all the recommended **backups**
  - Try to **follow these instructions** as closely as possible


This page is divided in three sections:

1. Preparatory tasks that should be performed before upgrading.
2. Detailed steps to actually perform the upgrade.
3. Suggested tasks to fine tune the setup after upgrading.


.. _upgrading#preparatory-tasks:

Preparatory tasks
-----------------

Before upgrading Pootle to a newer version, make sure to go through this
checklist.

* Familiarize yourself with :doc:`important changes </releases/index>` in
  Pootle.

* If you want to change the database backend then have a look at the
  :doc:`database migration <database_migration>` page first. We discourage
  using SQLite, so if you are using it please migrate to a real database
  server.

* Ensure that you meet the :ref:`hardware requirements
  <installation#hardware_requirements>` for the newer version.

* Always make backups of all your translation files (your whole
  :setting:`POOTLE_TRANSLATION_DIRECTORY`). Use the :djadmin:`sync_stores`
  command to synchronize all your translation files to disk before making any
  backup.

* Also backup your settings, to avoid losing any settings customizations.

* Make a backup of your complete database using the appropriate *dump*
  command for your database system. For example :command:`mysqldump` for MySQL,
  or :command:`pg_dump` for PostgreSQL.

* And don't forget to backup any code, templates or styling customization that
  you have done to your installation.

* Familiarize yourself with any new :ref:`settings <settings#available>` that
  have been introduced.


.. _upgrading#upgrading:

Upgrading
---------

Upgrading Pootle using the :command:`pip`.

.. note:: You will need to adjust these instructions if you installed Pootle
   using another method, such as directly from a Git checkout.

.. warning::

   Always backup the following before upgrading:

   - the entire **database**
   - all the **settings**
   - all your **translation files**
   - any **code customizations**
   - any **templates customizations**
   - any **styling customizations**


To perform the upgrade follow the next steps:

* If you want to perform a :doc:`database migration <database_migration>` then
  do it first.

* We highly recommended that you use a virtual environment. If your install
  currently doesn't use one then please :ref:`set up a virtualenv
  <installation#setup_environment>`.

* If you are upgrading from a version older than Pootle 2.7.0, then you must
  first upgrade to Pootle 2.6.0.

  .. code-block:: bash

     (env) $ pip install --upgrade "Pootle>=2.6,<2.7"
     (env) $ pootle setup


  .. note::

     If you weren't using a virtualenv before upgrading, instead of upgrading
     you will be just doing a fresh install of Pootle in a blank virtualenv:

     .. code-block:: bash

       (env) $ pip install "Pootle>=2.6,<2.7"
       (env) $ pootle setup


  Then continue with the upgrade process.

* Upgrade the Pootle package:

  .. code-block:: bash

     (env) $ pip install --upgrade Pootle


  .. note::

     If you weren't using a virtualenv before upgrading, instead of upgrading
     you will be just doing a fresh install of Pootle in a blank virtualenv:

     .. code-block:: bash

       (env) $ pip install Pootle


* Update your custom Pootle settings to adjust for any changes and to include
  any new settings. Delete any obsolete settings. Check the :ref:`available
  settings <settings#available>` as needed.

  .. note:: Running :djadmin:`pootle check` is helpful to highlight settings
     that have been obsoleted or renamed.

  .. note:: If you are upgrading from a version of Pootle that uses
     :file:`localsettings.py` then you must :ref:`move your custom settings
     <settings#customizing>` to a new location in order to ensure that Pootle
     uses them.

* Perform the database schema and data upgrade by running:

  .. code-block:: bash

     (env) $ pootle migrate


* Reapply your custom changes to Pootle code, templates or styling. Read about
  :doc:`customization of style sheets and templates
  </developers/customization>` to adjust your customizations to the correct
  locations and approach in the new release.

  .. note:: If you have customized the CSS styling or the JavaScript code you
     will have to run the following commands to update the static assets:

     .. code-block:: bash

       (env) $ cd $pootle_dir/pootle/static/js/
       (env) $ npm install
       (env) $ npm update
       (env) $ pootle webpack
       (env) $ pootle collectstatic --noinput --clear -i node_modules -i *.jsx
       (env) $ pootle assets build


     ``$pootle_dir`` is the directory where :command:`pip` installed Pootle. Its
     location depends on your settings for :command:`pip`, but by default it
     should be :file:`~/.virtualenvs/env/lib/python2.7/site-packages/`.


* Finally, restart your server.


.. _upgrading#post-upgrade:

Post-upgrade adjustments
------------------------

After a succesful upgrade you can now consider:

* Implementing some :doc:`optimizations <optimization>` to your setup.
* Creating a :ref:`Local Translation Memory
  <translation_memory#local_translation_memory>`.
