.. _changelog:

Changelog
=========

These are the critical changes that have happened in Pootle and may affect
your server. Also be aware of the :ref:`important changes in the
Translate Toolkit <toolkit:changelog>` as many of these also affect Pootle.

If you are upgrading Pootle, you might want to see some tips to ensure your
:ref:`upgrade goes smoothly <upgrading>`


Version 2.5.2
-------------

Not released yet. *Planned release date late April 2014*

- Local Translation Memory (TM) augments the already available `Amagama
  <http://amagama.translatehouse.org>`_ TM by delivering TM results from the
  projects hosted on the Pootle server.  Images stored in
  :setting:`PODIRECTORY` ``$project/.pootle/icon.png`` provide an icon to the
  TM result.

Version 2.5.1
-------------

Not released yet. *Planned release date late November 2013*

- The minimum required Python version is now 2.6.x. While Django 1.4.x supports
  Python 2.5, Python 2.5 is itself no longer supported by the Python Foundation
  neither by several third party apps, and supporting it requires an increasing
  number of ad-hoc patches on Pootle, so support for Python 2.5 on Pootle has
  been dropped.

- The minimum required Django version is 1.4.x.

- The database schema upgrade procedure has been redefined, and the
  :command:`updatedb` management command has been phased out in favor of
  South's own :ref:`migrate command <south:commands>`.  Post schema upgrade
  actions have been moved to the :command:`upgrade` command. For detailed
  instructions, read the :doc:`upgrading <server/upgrading>` section of the
  documentation.

- The :command:`setup` management command was added to hide the complexities in
  the initialization or upgrading of the DB when either upgrading or installing
  Pootle. Please read the :doc:`upgrading <server/upgrading>` and
  :doc:`installation <server/installation>` sections of the documentation.

- *css/custom/custom.css* is now served as part of the common bundle.

- The quality check for spell checking has been globally disabled. It wasn't
  properly advertised nor documented, and it didn't perform well enough to be
  considered useful.

- Pootle now supports tags that can be added to translation projects or
  individual files, and supports filtering translation projects by their tags.

- Pootle now supports goals that can be applied to files. It is possible to
  apply goals globally in a given project. Goals allow managers to provide a
  simple way to prioritize work and keep track of the translation progress in a
  group of files.

- Pootle allows custom scripts to be exposed in the Actions menu for a project.


Version 2.5.0
-------------

Major release, released on May 18th 2013.

- The minimum required Django version is 1.3.

- Static files are now handled by the ``django.contrib.staticfiles`` module.
  This means you will need to run the ``pootle collectstatic`` command on
  production and serve the *pootle/assets/* directory from your webserver at
  */assets/*. If you are upgrading from a previous version, you will need to
  replace the occurrences of *static* with *assets* within your web server
  configuration.

- Static files are bundled into assets by using `django-assets
  <http://elsdoerfer.name/docs/django-assets/>`_.

- Several features from translation projects have been merged into the
  *Overview* tab, including quality check failures and directory- and
  file-level actions. As a consequence the *Review* tab has been dropped and
  the *Translate* tab serves solely to display the actual translation
  editor.

- Settings have been migrated from *localsettings.py* into *settings/\*.conf*
  files. Your customizations now go in a :ref:`separate configuration file
  <settings#customizing>` (or in *settings/90-local.conf* if running from a
  repository clone).

- A new setting, :setting:`VCS_DIRECTORY` has been added, and VCS repositories
  are located in that directory, separate from the translation files used for
  editing and upload/download. The files in the VCS directory should never have
  any uncommitted changes in them, except during commit operations themselves.

- The ``PootleServer`` script has been phased out in favor of a ``pootle``
  runner script.

- If you will be using Pootle with Django 1.3, you *have* to keep the timezone
  on ``UTC``, unless you are using PostgreSQL. Users of PostgreSQL or Django
  1.4 or later are free to set the time zone as they prefer.
  Also make sure to use the minimum required South version when performing
  database upgrades.

- The ``update_from_templates`` management command has been renamed to
  :command:`update_against_templates`.

Version 2.1.6
-------------

Bugfix release, released on April 13th 2011.

- This is the first version that is compatible with Django 1.2.5 and
  Django 1.3.

- You also need Translate Toolkit 1.9.0 to be able to use these newer
  versions of Django.
