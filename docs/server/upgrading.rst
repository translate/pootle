.. _upgrading:

Upgrading
=========

.. warning::

  **Pootle 2.6.0 is just an intermediate upgrade step towards newer releases.**

  Pootle 2.6.0 is meant to be only used as an intermediate step for upgrading
  older Pootle deployments to the newer Pootle releases.


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
tells you how to continue with the upgrade to the next version, since Pootle
2.6.0 is only an intermediate upgrade step.


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

      (env)$ pip install Pootle==2.6.0


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


.. _upgrading#continue-the-upgrade:

Continue the upgrade to a newer version
---------------------------------------

Since Pootle 2.6.0 is intended to be an intermediate upgrade step towards newer
Pootle releases you will have to upgrade again to the desired version. In order
to do that just follow the upgrade instructions for that version.

.. warning::

  Please note that if you have some custom changes to Pootle code, templates or
  styling you will have to reapply those **after** finishing the upgrade to the
  desired Pootle version. Instructions on how to do that are available on the
  upgrade instructions.
