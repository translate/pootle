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
