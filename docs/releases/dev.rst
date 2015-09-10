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
- Changed user delete behaviour


Below we provide much more detail. These are by no means exhaustive, view the
`git log <https://github.com/translate/pootle/compare/stable/2.7.0...master>`_
for complete information.


Details of changes
==================

- Last activity snippets for stats are not kept in the cache anymore. The markup
  is now built on the client. This requires refreshing all server stats using
  the :djadmin:`refresh_stats` command (:issue:`3835`).

- Disabled projects are visually differentiated in the projects drop-down
  (:issue:`3996`).
  Since the in-cache data structure supporting this changed, it's necessary to
  clear the cache. Assuming your ``default`` cache lives in the DB number ``1``,
  you can clear it as follows:

  .. code-block:: bash

    $ redis-cli -n 1 KEYS "*method-cache:Project:cached_dict:*" | xargs redis-cli -n 1 DEL

- Pulled latest translations.


Django transaction hooks
------------------------

- To ensure async jobs are scheduled at the correct time
  `django-transaction-hooks
  <https://pypi.python.org/pypi/django-transaction-hooks/>`_ is now required.
  This dependency will be unnecessary once Django 1.9 becomes Pootle's minimum
  requirement.

- You must update your database connection to use one of the
  django-transaction-hooks backends:

  - mysql: transaction_hooks.backends.mysql
  - postgres: transaction_hooks.backends.postgresql_psycopg2


Changed user delete behaviour
-----------------------------

On deleting a user account their submissions, suggestions and reviews are now
re-assigned to the "nobody" user.

If you wish to remove the user's contributions also, you can use the
:djadmin:`purge_user` command, or call ``user.delete(purge=True)`` to delete the
user programatically.


Command changes and additions
-----------------------------

- Added a :djadmin:`contributors` command to get the list of contributors
  (:issue:`3867`).

- Added a :djadmin:`find_duplicate_emails` command to find duplicate emails.

- Added a :djadmin:`merge_user` command to get merge submissions, comments and
  reviews from one user account to another. This is useful for fixing users
  that have multiple accounts and want them to be combined. No profile data
  is merged.

- Added a :djadmin:`purge_user` command to purge a user from the site and revert
  any submissions, comments and reviews that they have made. This is useful to
  revert spam or a malicious user.

- Added a :djadmin:`verify_user` command to automatically verify a user account

- Renamed ``refresh_stats_rq`` command to :djadmin:`refresh_stats`, replacing the
  old command of the same name.

- Added a :djadmin:`update_user_email` command to update a user's email
  address.

- Added a :option:`--no-rq` option to run commands in a single process without
  using RQ workers.

...and lots of refactoring, cleanups to remove old Django versions specifics,
improved documentation and of course, loads of bugs were fixed.


Credits
=======

This release was made possible by the following people:

%CONTRIBUTORS%

And to all our bug finders, testers and translators, a Very BIG Thank You.
