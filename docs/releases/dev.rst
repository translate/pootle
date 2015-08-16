=====================================
Welcome to the new Pootle 2.7.1 alpha
=====================================

*Not yet released*

Bugfix release for 2.7.0.


Changes in Requirements
=======================
- Django >= 1.7, < 1.8
- Translate Toolkit >= 1.13.0
- Python >= 2.7, < 3.0
- Redis >= 2.8
- Django transaction hooks
- Unix-based operating system.


Major Changes
=============

- Updated translations.
- Added django-transaction-hooks


Below we provide much more detail. These are by no means exhaustive, view the
`git log <https://github.com/translate/pootle/compare/stable/2.7.0...master>`_
for complete information.


Details of changes
==================

- Last activity snippets for stats are not kept in the cache anymore. The markup
  is now built on the client. This requires refreshing all server stats using
  the :djadmin:`refresh_stats_rq` command (:issue:`3835`).

- Pulled latest translations.


Django transaction hooks
------------------------

- To ensure async jobs are scheduled at the correct time
  `django-transaction-hooks <https://pypi.python.org/pypi/django-transaction-hooks/>`_
  is now required. This will become unnecessary once we move to Django 1.9.

- You must update your database connection to use one of the
  django-transaction-hooks backends:

  - sqlite: transaction_hooks.backends.sqlite3
  - mysql: transaction_hooks.backends.mysql
  - postgres: transaction_hooks.backends.postgresql_psycopg2


Command changes and additions
-----------------------------

- Added a :djadmin:`contributors` command to get the list of contributors
  (:issue:`3867`).


...and lots of refactoring, cleanups to remove old Django versions specifics,
improved documentation and of course, loads of bugs were fixed.


Credits
=======

This release was made possible by the following people:

%CONTRIBUTORS%

And to all our bug finders, testers and translators, a Very BIG Thank You.
