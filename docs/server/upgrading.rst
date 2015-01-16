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
