.. _commands:

Management commands
===================

The management commands are administration commands provided by Django, Pootle
or any external Django app being used with Pootle. You will usually run these
commands by issuing ``pootle <command> [options]``.

For example, to get information about all available management commands, you
will run:

.. code-block:: console

    $ pootle help

.. note::

  If you run Pootle from a repository checkout you can use the *manage.py* file
  found in the root of the repository.


.. _commands#managing_pootle_projects:

Managing Pootle projects
------------------------

These commands will go through all existing projects performing maintenance
tasks. The tasks are all available through the web interface but on a project
by project or file by file basis.

.. django-admin-option:: --project, --language

The commands target can be limited in a more flexible way using the
:option:`--project` :option:`--language` command line options. They can be
repeated to indicate multiple languages or projects. If you use both options
together it will only match the files that match both languages and projects
selected.

For example, to *refresh_stats* for the tutorial project only, run:

.. code-block:: console

    $ pootle refresh_stats --project=tutorial

To only refresh a the Zulu and Basque language files within the tutorial
project, run:

.. code-block:: console

    $ pootle refresh_stats --project=tutorial --language=zu --language=eu


Running commands with --no-rq option
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. django-admin-option:: --no-rq

.. versionadded:: 2.7.1

Some of the commands work asynchronously and will schedule jobs to RQ workers,
rather than running them in the command process. You can change this behaviour
using the :option:`--no-rq` command line option.

This can be useful for running pootle commands in bash scripts or automating
installation/upgrade/migration. It can also be useful for debugging otherwise
asynchronous jobs.

For example, to run :djadmin:`refresh_stats` in the command process and wait
for the process to terminate:

.. code-block:: console

    $ pootle refresh_stats --no-rq

It is *not* generally safe to run commands in this mode if you have RQ workers
active at the same time, as there is a risk that they conflict with other jobs
dispatched to the workers.

.. django-admin-option:: --noinput

If there are RQ workers running, the command will ask for confirmation before
proceeding. This can be overridden using the :option:`--noinput` flag, in
which case the command will run even if there are.


.. django-admin:: refresh_stats

refresh_stats
^^^^^^^^^^^^^

Refreshes all calculated statistics ensuring that they are up-to-date.

A background process will create a task for every file to make sure calculated
statistics data is up to date. When the task for a file completes then further
tasks will be created for the files parents.

.. note:: Files in disabled projects are processed.

This command allows statistics to be updated when using multiple RQ workers.

.. warning:: Please note that the actual translations **must be in Pootle**
   before running this command. :djadmin:`update_stores` will pull them in.


.. django-admin:: retry_failed_jobs

retry_failed_jobs
^^^^^^^^^^^^^^^^^

.. versionadded:: 2.7

Requeue failed RQ jobs.

Background RQ jobs can fail for various reasons.  To push them back into the
queue you can run this command.

Examine the RQ worker logs for tracebacks before trying to requeue your jobs.


.. django-admin:: calculate_checks

calculate_checks
^^^^^^^^^^^^^^^^

.. versionadded:: 2.7

This command will create a background job to go through all units and
recalculate quality checks.

.. note:: Disabled projects are processed.

:djadmin:`calculate_checks` will flush existing caches and update the quality
checks cache.

It's necessary to run this command after upgrading Pootle if new quality
checks are added.

The time it takes to complete the whole process will vary depending on the
number of units you have in the database. If a user hits a page that needs to
display stats but they haven't been calculated yet, then a message will be
displayed indicating that the stats being calculated.

.. django-admin-option:: --check

Use the :option:`--check` option to force calculation of a specified check.  To
recalculate only the ``date_format`` quality checks, run:

.. code-block:: console

    $ pootle calculate_checks --check=date_format

Multiple checks can be specifed in one run as well:

.. code-block:: console

    $ pootle calculate_checks --check=date_format --check=accelerators


.. django-admin:: clear_stats

clear_stats
^^^^^^^^^^^

.. versionadded:: 2.7

Clear stats cache data.

Make use of :djadmin:`clear_stats` in cases where you want to remove all stats
data. Such a case may be where you want to recalculate stats after a change
to checks or wordcount calculations.  While it should be fine to run
:djadmin:`refresh_stats` or :djadmin:`calculate_checks`, by first running
:djadmin:`clear_stats` you can be sure that the stats are calculated from
scratch.


.. django-admin:: flush_cache

flush_cache
^^^^^^^^^^^

.. versionadded:: 2.8.0

Flush cache.

.. warning:: You must first **stop the workers** if you flush `stats`
   or `redis` cache.

.. django-admin-option:: --django-cache

Use the :option:`--django-cache` to flush the ``default`` cache which keeps
Django templates, project permissions etc.

.. django-admin-option:: --rqdata

Use the :option:`--rqdata` to flush all data contained in ``redis`` cache:
pending jobs, dirty flags, revision (which will be automatically restored),
all data from queues.

.. django-admin-option:: --stats

Use the :option:`--stats` to flush all stats data only (it works faster than
:djadmin:`clear_stats` but it requires stopping the worker).

.. django-admin-option:: --all

Use the :option:`--all` to flush all caches (``default``, ``redis``, ``stats``)
data.


.. django-admin:: refresh_scores

refresh_scores
^^^^^^^^^^^^^^

.. versionadded:: 2.7

Recalculates the scores for all users.

.. django-admin-option:: --reset

When the :option:`--reset` option is used , all score log data is removed and
`zero` score is set for all users.


.. django-admin:: sync_stores

sync_stores
^^^^^^^^^^^

.. versionchanged:: 2.7

Save all translations currently in the database to the file system, thereby
bringing the files under the :setting:`POOTLE_TRANSLATION_DIRECTORY` directory
in sync with the Pootle database.

.. note:: Disabled projects are skipped.

You must run this command before taking backups or running scripts that modify
the translation files directly on the file system, otherwise you might miss out
on translations that are in the database but not yet saved to disk. In
other words, **translations are saved to disk only when you explicitly do
so** using this command.

For every file being synced, the in-DB ``Store`` will be updated to
reflect the latest revision across the units in the file at the time of
syncing. This allows Pootle to make optimizations when syncing and
updating files, ignoring files that haven't change.

The default behavior of :djadmin:`sync_stores` can be altered by specifying
these parameters:

.. django-admin-option:: --force

  Synchronizes files even if nothing changed in the database.

.. django-admin-option:: --overwrite

  Copies the current state of the DB stores (not only translations, but also
  metadata) regardless if they have been modified since the last sync or
  not. This operation will (over)write existing on-disk files.

.. django-admin-option:: --skip-missing

  Ignores files missing on disk, and no new files will be created.


.. django-admin:: update_stores

update_stores
^^^^^^^^^^^^^

.. versionchanged:: 2.7

The opposite of :djadmin:`sync_stores`, this will update the strings in the
database to reflect what is on disk, as Pootle will not detect changes in the
file system on its own.

.. note:: Disabled projects are skipped.

It also discovers new units, files and translation projects that were
added on disk:

- Projects that exist in the DB but ceased to exist on disk will
  be **disabled** (not deleted). If a project is recovered on disk it can be
  enabled via the admin UI only.

- Translation projects will be scanned for new files and
  directories. In-DB files and directories that no longer exist on disk
  will be **marked as obsolete**. Also any in-DB directory will be
  **marked as obsolete** if this directory is empty or contains empty
  directories only.

- In-DB stores will be updated with the contents of the on-disk files.
  New units will be **added** to the store, units that ceased to exist
  will be **marked as obsolete**. Translations that were updated on-disk
  will be reflected in the DB.

You must run this command after running scripts that modify translation files
directly on the file system.

:djadmin:`update_stores` accepts several options:

.. django-admin-option:: --force

  Updates in-DB translations even if the on-disk file hasn't been changed
  since the last sync operation.

.. django-admin-option:: --overwrite

  Mirrors the on-disk contents of the file. If there have been changes in
  the database **since the last sync operation**, these will be
  overwritten.

.. warning:: If files on the file system are corrupt, translations might be
   deleted from the database. Handle with care!


.. django-admin:: list_languages

list_languages
^^^^^^^^^^^^^^

Lists all the language codes for languages hosted on the server. This can be
useful for automation.

.. django-admin-option:: --modified-since

Accepts the :option:`--modified-since` parameter to list only those languages
modified since the revision given by :djadmin:`revision`.


.. django-admin:: list_projects

list_projects
^^^^^^^^^^^^^

Lists all the project codes on the server. This might can be useful for
automation.

.. django-admin-option:: --modified-since

Accepts the :option:`--modified-since` parameter to list only those projects
modified since the revision given by :djadmin:`revision`.


.. django-admin:: contributors

contributors
^^^^^^^^^^^^

.. versionadded:: 2.7.1

Lists the contributors to a language, project or overall and the amount
of contributions they have.

Available options:

.. django-admin-option:: --from-revision

  Tells to only take into account contributions newer than the specified
  revision.

  Default: ``0``.

.. django-admin-option:: --sort-by

  .. versionadded:: 2.7.3

  Specifies the sorting to be used. Valid options are ``contributions`` (sort
  by decreasing number of contributions) and ``name`` (sort by user name,
  alphabetically).

  Default: ``name``.

.. django-admin-option:: --only-emails

  .. versionadded:: 2.8.0

  Specifies to only output user names and emails. Users with no email are
  skipped.

.. django-admin-option:: --since

  .. versionadded:: 2.8.0

  Only consider contributions since the specified date. Date must be in ISO
  8601 format (``2016-01-24T23:15:22+0000``) or be a string formatted like
  ``"2016-01-24 23:15:22 +0000"`` (quotes included).

  :option:`--since <contributors --since>` and
  :option:`--from-revision <contributors --from-revision>` are mutually
  exclusive.


.. django-admin:: revision

revision
^^^^^^^^

.. versionadded:: 2.7

Print the latest revision number.

The revision is a common system-wide counter for units. It is incremented with
every translation action made from the browser. Zero length units that have
been auto-translated also increment the unit revision.

.. django-admin-option:: --restore

The revision counter is stored in the database but also in cache for faster
retrieval. If for some reason the revision counter was removed or got
corrupted, passing the :option:`--restore` flag to the command will restore the
counter's value based on the revision data available on the relational DB
backend. You shouldn't need to ever run this, but if for instance you deleted
your cache you will need to restore the counter to ensure correct operation.


.. django-admin:: changed_languages

changed_languages
^^^^^^^^^^^^^^^^^

.. versionadded:: 2.7

Produces a comma-separated list of language codes that changed since the last
sync operation.

.. django-admin-option:: --after-revision

When :option:`--after-revision` is specified with a revision number as an
argument, it will print the language codes for languages that have changed
since the specified revision.


.. django-admin:: test_checks

test_checks
^^^^^^^^^^^

.. versionadded:: 2.7

Tests any given string pair or unit against all or certain checks from the
command line. This is useful for debugging and developing new checks.

.. django-admin-option:: --source, --target

String pairs can be specified by setting the values to be checked in the
``--source=<"source_text">`` and ``--target="<target_text>"``
command-line arguments.

.. django-admin-option:: --unit

Alternatively, ``--unit=<unit_id>`` can be used to reference an existing
unit from the database.

.. django-admin-option:: --check

By default, :djadmin:`test_checks` tests all existing checks. When
``--check=<checkname>`` is set, only specific checks will be tested against.


.. django-admin:: dump

dump
^^^^

.. versionadded:: 2.7

Prints data or stats data (depending on :option:`--data` or :option:`--stats` option)
in specific format.

.. django-admin-option:: --data

::

  object_id:class_name
  8276:Directory	name=android	parent=/uk/	pootle_path=/uk/android/
  24394:Store	file=android/uk/strings.xml.po	translation_project=/uk/android/	pootle_path=/uk/android/strings.xml.po	name=strings.xml.pstate=2
  806705:Unit	source=Create Account	target=Створити аккаунт	source_wordcount=2	target_wordcount=2	developer_comment=create_account	translator_commentlocations=File:\nstrings.xml\nID:\ne82a8ea14a0b9f92b1b67ebfde2c16e9	isobsolete=False	isfuzzy=False	istranslated=True
  115654:Suggestion	target_f=Необхідна електронна адреса	user_id=104481

.. django-admin-option:: --stats

::

  pootle_path total,translated,fuzzy,suggestions,criticals,is_dirty,last_action_unit_id,last_updated_unit_id
  /uk/android/strings.xml.po  11126,10597,383,231,0,False,4710214,4735242
  /uk/android/widget/strings.xml.po  339,339,0,26,0,False,2277376,3738609
  /uk/android/widget/  339,339,0,26,0,False,2277376,3738609
  /uk/android/  11465,10936,383,257,0,False,4710214,4735242

This command can be used by developers to check if all data kept after
migrations or stats calculating algorithm was changed.


.. _commands#translation-memory:

Translation Memory
------------------

These commands allow you to setup and manage :doc:`Translation Memory
</features/translation_memory>`.


.. django-admin:: update_tmserver

update_tmserver
^^^^^^^^^^^^^^^

.. versionadded:: 2.7

.. versionchanged:: 2.7.3 Renamed ``--overwrite`` to :option:`--refresh`.
   Disabled projects' translations are no longer added by default. It is also
   possible to import translations from files.


Updates the ``local`` server in :setting:`POOTLE_TM_SERVER`.  The command
reads translations from the current Pootle install and builds the TM resources
in the TM server.

If no options are provided, the command will only add new translations to the
server.

.. django-admin-option:: --refresh

Use :option:`--refresh` to also update existing translations that have
been changed, besides adding any new translation.

.. django-admin-option:: --rebuild

To completely remove the TM and rebuild it adding all existing translations use
:option:`--rebuild`.

.. django-admin-option:: --tm

If no specific TM server is specified using :option:`--tm`, then the default
``local`` TM will be used. If the specified TM server doesn't exist it will
be automatically created for you.

.. django-admin-option:: --include-disabled-projects

By default translations from disabled projects are not added to the TM, but
this can be changed by specifying :option:`--include-disabled-projects`.

.. django-admin-option:: --dry-run

To see how many units will be loaded into the server use :option:`--dry-run`,
no actual data will be loaded or deleted (the TM will be left unchanged):

.. code-block:: console

    $ pootle update_tmserver --dry-run
    $ pootle update_tmserver --refresh --dry-run
    $ pootle update_tmserver --rebuild --dry-run


This command also allows to read translations from files and build the TM
resources in the external TM server. In order to do so it is mandatory to
provide the :option:`--tm` and :option:`--display-name` options, along with
some files to import.

.. django-admin-option:: --display-name

The display name is a label used to group translations within a TM. A given TM
can host translations for several display names. The display name can be used
to specify the name of the project from which the translations originate. The
display name will be shown on TM matches in the translation editor. To specify
a name use :option:`--display-name`:

.. code-block:: console

   (env) $ pootle update_tmserver --tm=libreoffice --display-name="LibreOffice 4.3 UI" TM_LibreOffice_4.3.gl.tmx


By default the command will only add new translations to the server. To rebuild
the server from scratch use :option:`--rebuild` to completely remove the TM and
rebuild it before importing the translations:

.. code-block:: console

   (env) $ pootle update_tmserver --rebuild --tm=mozilla --display-name="Foo 1.7" foo.po


Option :option:`--refresh` doesn't apply when adding translations from files
on disk.

To see how many units will be loaded into the server use :option:`--dry-run`,
no actual data will be loaded:

.. code-block:: console

   (env) $ pootle update_tmserver --dry-run --tm=mozilla --display-name="Foo 1.7" foo.po
   175045 translations to index


This command is capable of importing translations in multiple formats from
several files and directories at once:

.. code-block:: console

   (env) $ pootle update_tmserver --tm=mozilla --display-name="Foo 1.7" bar.tmx foo.xliff fr/


.. django-admin-option:: --target-language

Use :option:`--target-language` to specify the target language ISO code for the
imported translations in case it is not possible to guess it from the
translation files or if the code is incorrect:

.. code-block:: console

   (env) $ pootle update_tmserver --target-language=af --tm=mozilla --display-name="Foo 1.7" foo.po bar.tmx


.. _commands#vfolders:

Virtual Folders
---------------

These commands allow you to perform tasks with virtual folders from the command
line.


.. django-admin:: add_vfolders

add_vfolders
^^^^^^^^^^^^

.. versionadded:: 2.7

Creates :ref:`virtual folders <virtual_folders>` from a JSON file. If the
specified virtual folders already exist then they are updated.

The :ref:`vfolder format <virtual_folders#json-format>` defines how to specify
a virtual folder that fits your needs.

This command requires a mandatory filename argument.

.. code-block:: console

    $ pootle add_vfolders virtual_folders.json


.. _commands#import_export:

Import and Export
-----------------

Export and Import translation files in Pootle.  The operation can be thought of
best as offline operations to assist with offline translation, unlike
:djadmin:`sync_stores` and :djadmin:`update_stores` the operations here are
designed to cater for translators working outside of Pootle.

The :djadmin:`import` and :djadmin:`export` commands are designed to mimic the
operations of Download and Upload from the Pootle UI.

.. django-admin:: export

export
^^^^^^

.. versionadded:: 2.7

Download a file for offline translation.

.. note:: This mimics the editor's download functionality and its primary
   purpose is to test the operation of downloads from the command line.

A file or a .zip of files is provided as output.  The file headers include a
revision counter to assist Pootle to detetmine how to handle subsequent uploads
of the file.

.. django-admin:: import

import
^^^^^^

.. versionadded:: 2.7

Upload a file that was altered offline.

.. note:: This mimics the editor's upload functionality and its primary purpose
   is to test the operation of uploads from the command line.

A file or a .zip is submitted to Pootle and based on the revision counter of
the ``Store`` on Pootle it will be uploaded or rejected.  If the revision
counter is older than on Pootle, that is someone has translated while the file
was offline, then it will be rejected.  Otherwise the translations in the file
are accepted.

Available options:

.. django-admin-option:: --user

  .. versionadded:: 2.7.3

  Import file(s) as given user. The user with the provided username must exist.

  Default: ``system``.


.. _commands#manually_installing_pootle:

Manually Installing Pootle
--------------------------

These commands expose the database installation and upgrade process from the
command line.

.. django-admin:: init

init
^^^^

Create the initial configuration for Pootle.

Available options:

.. django-admin-option:: --config
  The configuration file to write to.

  Default: ``~/.pootle/pootle.conf``.

.. django-admin-option:: --db

  .. versionadded:: 2.7.1

  The database backend that you are using

  Default: ``sqlite``.
  Available options: ``sqlite``, ``mysql``, ``postgresql``.

.. django-admin-option:: --db-name

  .. versionadded:: 2.7.1

  The database name or path to database file if you are using sqlite.

  Default for sqlite: ``dbs/pootle.db``.
  Default for mysql/postgresql: ``pootledb``.

.. django-admin-option:: --db-user

  .. versionadded:: 2.7.1

  Name of the database user. Not used with sqlite.

  Default: ``pootle``.

.. django-admin-option:: --db-host

  .. versionadded:: 2.7.1

  Database host to connect to. Not used with sqlite.

  Default: ``localhost``.

.. django-admin-option:: --db-port

  .. versionadded:: 2.7.1

  Port to connect to database on. Defaults to database backend's default port.
  Not used with sqlite.


.. django-admin:: initdb

initdb
^^^^^^

Initializes a new Pootle install.

This is an optional part of Pootle's install process, it creates the default
*admin* user, populates the language table with several languages, initializes
the terminology project, and creates the tutorial project among other tasks.

:djadmin:`initdb` can only be run after :djadmin:`django:migrate`.

:djadmin:`initdb` accepts the following option:

.. versionadded:: 2.7.3

.. django-admin-option:: --no-projects

   Don't create the default ``terminology`` and ``tutorial`` projects.

.. note:: :djadmin:`initdb` will import translations into the database, so
   can be slow to run. You should have an ``rqworker`` running or run with
   the `--no-rq`.


.. _commands#collectstatic:

collectstatic
^^^^^^^^^^^^^

Running the Django admin :djadmin:`django:collectstatic` command finds and
extracts static content such as images, CSS and JavaScript files used by the
Pootle server, so that they can be served separately from a static webserver.
Typically, this is run with the ``--clear`` ``--noinput`` options, to flush any
existing static data and use default answers for the content finders.


.. _commands#assets:

assets
^^^^^^

Pootle uses the Django app `django-assets`_ interface of `webassets` to minify
and bundle CSS and JavaScript; this app has a management command that is used
to make these preparations using the command ``assets build``. This command is
usually executed after the :ref:`collectstatic <commands#collectstatic>` one.


.. django-admin:: webpack

webpack
^^^^^^^

.. versionadded:: 2.7

The `webpack <http://webpack.github.io/>`_ tool is used under the hood to
bundle JavaScript scripts, and this management command is a convenient
wrapper that sets everything up ready for production and makes sure to
include any 3rd party customizations.

.. django-admin-option:: --dev

When the :option:`--dev` flag is enabled, development builds will be created
and the process will start a watchdog to track any client-side scripts for
changes. Use this only when developing Pootle.


.. _commands#user-management:

Managing users
--------------


.. django-admin:: find_duplicate_emails

find_duplicate_emails
^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 2.7.1

As of Pootle version 2.8, it will no longer be possible to have users with
duplicate emails. This command will find any user accounts that have duplicate
emails. It also shows the last login time for each affected user and indicates
if they are superusers of the site.

.. code-block:: console

    $ pootle find_duplicate_emails


.. django-admin:: merge_user

merge_user
^^^^^^^^^^

.. versionadded:: 2.7.1

This can be used if you have a user with two accounts and need to merge one
account into another. This will re-assign all submissions, units and
suggestions, but not any of the user's profile data.

This command requires 2 mandatory arguments, ``src_username`` and
``target_username``, both should be valid usernames for users of your site.
Submissions from the first are re-assigned to the second. The users' profile
data is not merged.

.. django-admin-option:: --no-delete

By default ``src_username`` will be deleted after the contributions have been
merged. You can prevent this by using the :option:`--no-delete` option.

.. code-block:: console

    $ pootle merge_user src_username target_username


.. django-admin:: purge_user

purge_user
^^^^^^^^^^

.. versionadded:: 2.7.1

This command can be used if you wish to permanently remove a user and revert
the edits, comments and reviews that the user has made. This is useful for
removing a spam account or other malicious user.

This command requires a mandatory ``username`` argument, which should be a valid
username for a user of your site.

.. versionchanged:: 2.7.3 :djadmin:`purge_user` can accept multiple user
   accounts to purge.

.. code-block:: console

    $ pootle purge_user username [username ...]


.. django-admin:: update_user_email

update_user_email
^^^^^^^^^^^^^^^^^

.. versionadded:: 2.7.1


.. code-block:: console

    $ pootle update_user_email username email

This command can be used if you wish to update a user's email address. This
might be useful if you have users with duplicate email addresses.

This command requires a mandatory ``username``, which should be a valid
username for a user of your site, and a mandatory valid ``email`` address.

.. code-block:: console

    $ pootle update_user_email username email


.. django-admin:: verify_user

verify_user
^^^^^^^^^^^

.. versionadded:: 2.7.1

Verify a user without the user having to go through email verification process.

This is useful if you are migrating users that have already been verified, or
if you want to create a superuser that can log in immediately.

This command requires either mandatory ``username`` arguments, which should be
valid username(s) for user(s) on your site, or the :option:`--all` flag if you
wish to verify all users of your site.

.. versionchanged:: 2.7.3 :djadmin:`verify_user` can accept multiple user
   accounts to verify.

.. code-block:: console

    $ pootle verify_user username [username ...]

Available options:

.. django-admin-option:: --all

  Verify all users of the site


.. _commands#running:

Running WSGI servers
--------------------

There are multiple ways to run Pootle, and some of them rely on running WSGI
servers that can be reverse proxied to a proper HTTP web server such as nginx
or lighttpd.

There are many more options such as `uWSGI
<http://uwsgi-docs.readthedocs.org/en/latest/WSGIquickstart.html>`_, `Gunicorn
<http://gunicorn.org/>`_, etc.


.. _commands#deprecated:

Deprecated commands
-------------------

The following are commands that have been removed or deprecated:


.. django-admin:: last_change_id

last_change_id
^^^^^^^^^^^^^^

.. deprecated:: 2.7

With the change to revisions the command you will want to use is
:djadmin:`revision`, though you are unlikely to know a specific revision
number as you needed to in older versions of :djadmin:`update_stores`.


.. django-admin:: commit_to_vcs

commit_to_vcs
^^^^^^^^^^^^^

.. deprecated:: 2.7

Version Control support has been removed from Pootle and will reappear in a
later release.


.. django-admin:: update_from_vcs

update_from_vcs
^^^^^^^^^^^^^^^

.. deprecated:: 2.7

Version Control support has been removed from Pootle and will reappear in a
later release.


.. django-admin:: run_cherrypy

run_cherrypy
^^^^^^^^^^^^

.. deprecated:: 2.7.3

Run the CherryPy server bundled with the Translate Toolkit.


.. django-admin:: start

start
^^^^^

.. removed:: 2.7.3

Use :djadmin:`runserver` instead.

Run Pootle using the default Django server.


.. _commands#running_in_cron:

Running Commands in cron
------------------------

If you want to schedule certain actions on your Pootle server, using management
commands with cron might be a solution.

The management commands can perform certain batch commands which you might want
to have executed periodically without user intervention.

For the full details on how to configure cron, read your platform documentation
(for example ``man crontab``). Here is an example that runs the
:djadmin:`refresh_stats` command daily at 02:00 AM::

    00 02 * * * www-data /var/www/sites/pootle/manage.py refresh_stats

Test your command with the parameters you want from the command line. Insert it
in the cron table, and ensure that it is executed as the correct user (the same
as your web server) like *www-data*, for example. The user executing the
command is specified in the sixth column. Cron might report errors through
local mail, but it might also be useful to look at the logs in
*/var/log/cron/*, for example.

If you are running Pootle from a virtualenv, or if you set any custom
:envvar:`PYTHONPATH` or similar, you might need to run your management command
from a bash script that creates the correct environment for your command to run
from.  Call this script then from cron. It shouldn't be necessary to specify
the settings file for Pootle — it should automatically be detected.

.. _django-assets: http://django-assets.readthedocs.org/en/latest/

.. _webassets: http://elsdoerfer.name/docs/webassets/
