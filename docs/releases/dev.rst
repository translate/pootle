=====================================
Welcome to the new Pootle 2.7.3 final
=====================================

*Not yet released*

Bugfix release for 2.7.2.


Changes in Requirements
=======================
- Django >= 1.7.10, < 1.8
- Translate Toolkit >= 1.13.0
- Python >= 2.7, < 3.0
- Redis >= 2.8.4
- Django transaction hooks
- Unix-based operating system.


Major Changes
=============

- Pulled latest translations.
- Added support for Elasticsearch-based external Translation Memory servers.
- Cleaned up connection logic for Translation Memory servers
- Added checks for misconfigured Translation Memory servers
- Translation Projects are now loaded by initdb and stats are automatically
  generated.

Below we provide much more detail. These are by no means exhaustive, view the
`git log <https://github.com/translate/pootle/compare/2.7.2...2.7.3>`_ for
complete information.


Details of changes
==================

- The editor for static pages now highlights the content's markup and displays a
  live preview of the rendered contents (:issue:`3346`, :issue:`3766`).
- Pulled latest translations.
- :djadmin:`update_tmserver`:

  - Renamed :option:`--overwrite` to :option:`--refresh`.
  - Translations from disabled projects must be explicitly included with
    :option:`--include-disabled-projects`.
  - Added support for Elasticsearch-based external Translation Memory servers,
    which can be populated from translation files. This effectively brings the
    ability to display TM results from different TM servers, sorting them by
    their score.

- :setting:`POOTLE_TM_SERVER`:

  - The ``default`` TM server has been renamed to ``local``. Make sure to
    adjust your settings.
  - Added a new :setting:`WEIGHT <POOTLE_TM_SERVER-WEIGHT>` option to raise or
    lower the TM results score for each specific TM server.

- :djadmin:`import`:

  - Added a new :option:`--user` to allow setting of user to attribute changes to
    on file import.

- The Apertium MT backend has been dropped.
- Report string errors form subject and body can be overriden.
- `InnoDB <https://dev.mysql.com/doc/refman/5.6/en/innodb-storage-engine.html>`_
  is the only accepted MySQL backend. Deployments using MyISAM must
  :doc:`migrate to either MySQL (InnoDB) or PostgreSQL </server/database_migration>`.
- Close a database connection before and after each rqworker job once it exceeds
  the maximum age to imitate Django's request/response cycle.
- Language managers can now edit their language's special characters.
- :djadmin:`initdb` now has an :option:`--no-projects` to prevent creating
  the default projects at set up.

...and lots of refactoring, new tests, cleanups, improved documentation and of
course, loads of bugs were fixed.


Credits
=======

This release was made possible by the following people:

%CONTRIBUTORS%

And to all our bug finders, testers and translators, a Very BIG Thank You.
