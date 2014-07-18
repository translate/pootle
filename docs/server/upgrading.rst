.. _upgrading:

Upgrading
=========

Here are some points to take into account while performing Pootle
upgrades.

.. warning::

  Upgrading Pootle to a newer version can be a dangerous endeavour, so please:

  - **Carefully read this entire page** before proceeding with any further
    steps
  - Do all the recommended **backups**
  - Try to **follow these instructions** as must as possible


This page is divided in three sections. The first one lists some previous tasks
that should be performed before upgrading. The second section includes a
detailed list of steps to follow to actually perform the upgrade. The third one
suggests some possible tasks to fine tune the setup after upgrading.


.. _upgrading#previous-tasks:

Previous tasks
--------------

.. note::

  If you perform all the steps in this section you will:

  - Avoid losing any data or Pootle customizations,
  - Ensure a thorough and successful upgrade,
  - Prevent headaches for you and the support team.


Before upgrading Pootle to a newer version, make sure to go through this
checklist.

* Familiarize yourself with :doc:`important changes </releases/index>` in
  Pootle over the versions.

* If you want to change the database backed then have a look at the
  :doc:`database migration <database_migration>` page first.

* Ensure that you meet all the :ref:`hardware requirements
  <installation#hardware_requirements>` for the newer version.

* Always make backups of all your translation files (your whole
  :setting:`PODIRECTORY`). Use the :ref:`sync_stores <commands#sync_stores>`
  command to synchronize to disk all your translation files before making any
  backup.

* Also backup your settings, to avoid losing any settings customization.

* Make a backup of your complete database using the appropriate *dump*
  command for your database system. For example :command:`mysqldump` for MySQL,
  or :command:`pg_dump` for PostgreSQL.

* And don't forget to backup any code, templates or styling customization that
  you have done to your Pootle.

* You might want to look for any new :ref:`available settings
  <settings#available>` in the new version that you might want to configure.


.. _upgrading#upgrading:

Upgrading
---------

Here is the list of steps to upgrade a Pootle install using the :command:`pip`
tool.

.. note::

  Since these instructions don't take into account other possible installation
  methods, like using a checkout from git, you will have to do the appropriate
  adjustments in this list if you didn't install Pootle using :command:`pip`.

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
  do it right now.

* It is highly recommended to use a virtualenv, so if you don't use it please
  :ref:`set up a virtualenv <installation#setup_environment>`.

* Upgrade the Pootle package:

  .. code-block:: bash

    (env)$ pip install --upgrade Pootle==2.6.0


  .. note::

    If you weren't using a virtualenv before upgrading, instead of upgrading
    you will be just doing a fresh install of Pootle in a blank virtualenv:

    .. code-block:: bash

      (env)$ pip install Pootle


* Update Pootle settings to include new useful settings and updating existing
  ones, while keeping the necessary data from the old install. Deleting now
  unused settings is also advisable. Check the :ref:`available settings
  <settings#available>`.

  .. note::

    If you are upgrading from a version of Pootle that uses
    :file:`localsettings.py` then you must :ref:`move your custom settings
    <settings#customizing>` to a new location in order to ensure that Pootle
    uses them.


* Perform the database schema and data upgrade by running:

  .. code-block:: bash

    (env)$ pootle setup


* Reapply your custom changes to Pootle code, templates or styling. Check about
  the :doc:`customization of style sheets and templates
  </developers/customization>` to move your customizations to the right
  locations in order to reduce the pain in future upgrades.

* Run the :ref:`collectstatic <commands#collectstatic>` and :ref:`assets build
  <commands#assets>` commands to update the static assets:

  .. code-block:: bash

    (env)$ pootle collectstatic --clear --noinput
    (env)$ pootle assets build


* Finally clear your cache. For users of :command:`memcached` it is enough to
  restart it.


.. _upgrading#post-upgrade:

Post-upgrade adjustments
------------------------

After a succesful upgrade you can now consider :doc:`making some optimizations
to your setup <optimization>`, like for example using a real database or a
proper web server.

.. note::

  If you are already using some optimizations you might need to find out if you
  need to perform any adjustment or reload any server.


Also you might want to create a local Translation Memory. Have in mind that
this can take a lot of time depending on how many translations you have in your
Pootle database.

.. code-block:: bash

  (env)$ pootle create_local_tm


.. _upgrading#database:

Performing the Database Upgrade
-------------------------------

.. versionchanged:: 2.5.1

Once you have the new code configured to in your server using the correct
settings file, you will be ready to run the database schema and data
upgrade procedure.

Since the database upgrade procedures have been growing in complexity in the
last releases it was necessary to provide a simple way to upgrade Pootle using
a single command. The old procedure is still available, mostly for debugging
failing upgrades, but the new procedure is now the preferred one.


.. _upgrading#simplified-upgrade:

Simplified database upgrade
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::

  Always make database backups before running any upgrades.


This is now the preferred way to upgrade the database.

The procedure is easy, just run:

.. code-block:: bash

  $ pootle setup


.. note::

  After a succesful upgrade, you might want to create a local Translation
  Memory. Have in mind that this can take a lot of time depending on how many
  translations you have in your Pootle database.

  .. code-block:: bash

    $ pootle create_local_tm


.. _upgrading#detailed-upgrade:

Step by step database upgrade
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::

  Always make database backups before running any upgrades.


.. note::

  Use this procedure only if the :ref:`Simplified database upgrade
  <upgrading#simplified-upgrade>` procedure doesn't work for you.


.. warning::

  If you are upgrading from Pootle 2.1.0 or older you must first upgrade to
  2.1.6, before upgrading to this version.


The step by step database upgrade procedure lets you control the upgrade
process and tweak it. This is useful for debugging purposes.


.. note::

  If you are upgrading from a Pootle version older than 2.5.0, you will need
  an extra step at the beginning (before running ``syncdb --noinput``):

  .. code-block:: bash

    $ pootle updatedb


  The :ref:`updatedb command <commands#updatedb>` upgrades the database schema
  to the state of Pootle 2.5.0. This is necessary due to the changes made to
  the database schema migration mechanisms after the 2.5.0 release.


In the first step, the syncdb command will create any missing database tables
that don't require any migrations:

.. code-block:: bash

  $ pootle syncdb --noinput


For this specific version (Pootle 2.5.1), and due to Pootle's transitioning to
South, you will need to run a fake migration action in order to let South know
which is your current database schema. You can execute the fake migration by
running the following commands:

.. code-block:: bash

  $ pootle migrate pootle_app --fake 0001
  $ pootle migrate pootle_language --fake 0001
  $ pootle migrate pootle_notifications --fake 0001
  $ pootle migrate pootle_project --fake 0001
  $ pootle migrate pootle_statistics --fake 0001
  $ pootle migrate pootle_store --fake 0001
  $ pootle migrate pootle_translationproject --fake 0001


.. note::

  If you are upgrading from Pootle 2.5.0 you also have to run:

  .. code-block:: bash

    $ pootle migrate staticpages --fake 0001


The next step will perform any pending schema migrations. You can read more
about the :ref:`migrate command <south:commands>` in South's documentation.

.. code-block:: bash

  $ pootle migrate


Lastly, the :ref:`upgrade command <commands#upgrade>` will perform any extra
operations needed by Pootle to finish the upgrade and will record the current
code build versions for Pootle and the Translate Toolkit. Before running this
command please check if you are interested on running it using any of its
available flags.

.. code-block:: bash

  $ pootle upgrade


.. note::

  After a succesful upgrade, you might want to create a local Translation
  Memory. Have in mind that this can take a lot of time depending on how many
  translations you have in your Pootle database.

  .. code-block:: bash

    $ pootle create_local_tm


.. _upgrading#custom_changes:

Custom Changes
--------------

If you made any changes to Pootle code, templates or styling, you will want to
ensure that your upgraded Pootle contains those changes.  How hard that is will
depend entirely on the details of these changes.

Changes made to the base template are likely to work fine, but changes to
details will need individual inspection to see if they can apply
cleanly or have to be reimplemented on the new version of Pootle.

Since Pootle 2.5 :doc:`customization of style sheets and templates
</developers/customization>` have become much easier to seperate from the
standard code.  If you are migrating to Pootle 2.5+ then use this opportunity
to move your code to the correct customization locations.
