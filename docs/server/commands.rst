.. _commands:

Management commands
===================

The management commands are administration commands provided by Django, Pootle
or any external Django app being used with Pootle. You will usually run these
commands by issuing ``pootle <command> [options]``.

For example, to get information about all available management commands, you
will run:

.. code-block:: console

    (env) $ pootle help


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

For example, to *calculate_checks* for the tutorial project only, run:

.. code-block:: console

    (env) $ pootle calculate_checks --project=tutorial

To only calculate the Zulu and Basque language files within the tutorial
project, run:

.. code-block:: console

    (env) $ pootle calculate_checks --project=tutorial --language=zu --language=eu


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

For example, to run :djadmin:`calculate_checks` in the command process and wait
for the process to terminate:

.. code-block:: console

    (env) $ pootle calculate_checks --no-rq

It is *not* generally safe to run commands in this mode if you have RQ workers
active at the same time, as there is a risk that they conflict with other jobs
dispatched to the workers.

.. django-admin-option:: --atomic

.. versionadded:: 2.8

  Default: ``tp``.
  Available choices: ``tp``, ``all``, ``none``.

  This option allows you to run CLI commands with atomic transactions.

  The default is to commit changes on per-translation-project basis.

  For example to run update_stores against all translation projects in a single
  transaction.

.. code-block:: console

    (env) $ pootle update_stores --atomic=all



.. django-admin-option:: --noinput

If there are RQ workers running, the command will ask for confirmation before
proceeding. This can be overridden using the :option:`--noinput` flag, in
which case the command will run even if there are.


.. django-admin:: retry_failed_jobs

retry_failed_jobs
^^^^^^^^^^^^^^^^^

.. versionadded:: 2.7

Requeue failed RQ jobs.

Background RQ jobs can fail for various reasons.  To push them back into the
queue you can run this command.

Examine the RQ worker logs for tracebacks before trying to requeue your jobs.


.. django-admin:: update_data

update_data
^^^^^^^^^^^

.. versionadded:: 2.8

This command updates the stats data. The stats data update can be triggered for
specific languages or projects.

.. django-admin-option:: --store

Use the :option:`--store` option to narrow the stats data calculation to a
specific store:

.. code-block:: console

    (env) $ pootle update_data --store=/fr/proj/mydir/mystore.po

Note this will also trigger the update of the stats data for items above the
store, like for example directories above it, its language and its project.


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

    (env) $ pootle calculate_checks --check=date_format

Multiple checks can be specified in one run as well:

.. code-block:: console

    (env) $ pootle calculate_checks --check=date_format --check=accelerators


.. django-admin:: flush_cache

flush_cache
^^^^^^^^^^^

.. versionadded:: 2.8.0

Flush cache.

.. warning:: You must first **stop the workers** if you flush `redis` cache.

.. django-admin-option:: --django-cache

Use the :option:`--django-cache` to flush the ``default`` cache which keeps
Django templates, project permissions etc.

.. django-admin-option:: --rqdata

Use the :option:`--rqdata` to flush all data contained in ``redis`` cache:
pending jobs, revision (which will be automatically restored), all data from
queues.

.. django-admin-option:: --lru

Use the :option:`--lru` to flush all lru cache data contained
in ``lru`` cache.

.. django-admin-option:: --all

Use the :option:`--all` to flush all caches (``default``, ``redis``, ``lru``) data.


.. django-admin:: refresh_scores

refresh_scores
^^^^^^^^^^^^^^

.. versionadded:: 2.7

Recalculates the scores for all users. It is possible to narrow down the
calculation to specific projects and/or languages.

.. warning:: It is advisable to run this command while Pootle server is offline
   since the command can fail due to data being changed by users.


.. django-admin-option:: --reset

When the :option:`--reset` option is used , all score log data is removed and
`zero` score is set for all users.


.. django-admin:: sync_stores

sync_stores
^^^^^^^^^^^

.. deprecated:: 2.9
   Deprecated in favor of :ref:`Pootle FS equivalent
   <migrate_to_pootle_fs#replacing-update_stores-and-sync_stores>`.


.. note:: Since version 2.9 all projects are managed by Pootle FS and therefore
   this command is now able to work with those projects.


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

  .. versionchanged:: 2.9
     This option has no effect anymore.

.. django-admin-option:: --overwrite

  .. versionchanged:: 2.9
     This option has no effect anymore.

.. django-admin-option:: --skip-missing

  Ignores files missing on disk, and no new files will be created.


.. django-admin:: update_stores

update_stores
^^^^^^^^^^^^^

.. deprecated:: 2.9
   Deprecated in favor of :ref:`Pootle FS equivalent
   <migrate_to_pootle_fs#replacing-update_stores-and-sync_stores>`.


.. note:: Since version 2.9 all projects are managed by Pootle FS and therefore
   this command is now able to work with those projects.


Load translation files currently on the file system into the database, thereby
bringing the Pootle database in sync with the files under the
:setting:`POOTLE_TRANSLATION_DIRECTORY` directory.  Pootle will not detect
changes in the file system on its own.  This is the opposite of
:djadmin:`sync_stores`.

.. note:: Disabled projects are skipped.

.. note:: :djadmin:`update_stores` does not manage the updating of translations
   against templates, it simply loads translation files and translation
   templates into Pootle.  For a full understanding of the role of templates
   and updating translations against templates read the :doc:`templates
   </features/templates>` section.

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

  .. versionchanged:: 2.9
     This option has no effect anymore.

.. django-admin-option:: --overwrite

  Mirrors the on-disk contents of the file. If there have been changes in
  the database **since the last sync operation**, these will be
  overwritten.

.. warning:: If files on the file system are corrupt, translations might be
   deleted from the database. Handle with care!


.. django-admin:: list_serializers

list_serializers
^^^^^^^^^^^^^^^^

.. versionadded:: 2.8.0

List the installed serializers and deserializers on your system.

Available options:

.. django-admin-option:: -m, --model

List serializers for specified model. The model should be expressed as a
contenttype label - eg ``app_name``.``model_name``

.. django-admin-option:: -d, --deserializers

List available deserializers set up for our system.


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

.. django-admin-option:: --sort-by

  .. versionchanged:: 2.8.0

  Specifies the sorting to be used. Valid options are ``contributions`` (sort
  by decreasing number of contributions) and ``username`` (sort by user name,
  alphabetically).

  Default: ``username``.

.. django-admin-option:: --mailmerge

  .. versionadded:: 2.8.0

  Specifies to only output user names and emails. Users with no email are
  skipped.

  :option:`--mailmerge <contributors --mailmerge>` and
  :option:`--include-anonymous <contributors --include-anonymous>` are mutually
  exclusive.

.. django-admin-option:: --include-anonymous

  .. versionadded:: 2.8.0

  Specifies to include anonymous contributions.

  :option:`--include-anonymous <contributors --include-anonymous>` and
  :option:`--mailmerge <contributors --mailmerge>` are mutually exclusive.

.. django-admin-option:: --since

  .. versionadded:: 2.8.0

  Only consider contributions since the specified date or datetime.

  Date or datetime can be in any format accepted by ``python-dateutil``
  library, for example ISO 8601 format (``2016-01-24T23:15:22+0000`` or
  ``2016-01-24``) or a string formatted like ``"2016-01-24 23:15:22 +0000"``
  (quotes included).

.. django-admin-option:: --until

  .. versionadded:: 2.8.0

  Only consider contributions until the specified date or datetime.

  Date or datetime can be in any format accepted by ``python-dateutil``
  library, for example ISO 8601 format (``2016-01-24T23:15:22+0000`` or
  ``2016-01-24``) or a string formatted like ``"2016-01-24 23:15:22 +0000"``
  (quotes included).


.. django-admin:: set_filetype

set_filetype
^^^^^^^^^^^^

.. versionadded:: 2.8

This command sets file formats for projects, and also allows to convert files
to another format.

.. django-admin-option:: --from-filetype

Convert stores of this file type.

.. django-admin-option:: --matching

Convert stores matching this path glob within the project.


For example, to add the `properties` format to a project, run:

.. code-block:: console

    (env) $ pootle set_filetype --project=myproj properties


To convert stores of `po` format to `properties`, run:

.. code-block:: console

    (env) $ pootle set_filetype --project=myproj --from-filetype=po properties


To convert stores matching a given path glob to `properties` format, run:

.. code-block:: console

    (env) $ pootle set_filetype --project=myproj --matching=mydir/myfile-* properties


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



.. django-admin:: config

config
^^^^^^

.. versionadded:: 2.8

Gets, sets, lists, appends and clears pootle configuration settings.

.. django-admin-option:: content_type

  Optional positional argument to specify a model to manage configuration for.


.. django-admin-option:: object

  Optional positional argument to specify the primary key of an object to
  manage configuration for. You can use a field other than the primary key by
  specifying :option:`-o`, but the field must be unique for the
  request object when doing so.


.. django-admin-option:: -o <field>, --object-field <field>

  Specify a field other than the primary key when specifying an object. It must
  be unique to the object specified.


.. django-admin-option:: -g <key>, --get <key>

  Get value for specified key.


.. django-admin-option:: -l <key>, --list <key>

  List values for specified key(s). This option can be specified multiple times.


.. django-admin-option:: -s <key> <value>, --set <key> <value>

  Set value for specified key. The key must be unique or not exist already.


.. django-admin-option:: -a <key> <value>, --append <key> <value>

  Append value for specified key.


.. django-admin-option:: -c <key>, --clear <key>

  Clear value(s) for specified key.


.. django-admin-option:: -j, --json

  Treat data as JSON when getting, setting, or appending values.


.. django-admin:: schema

schema
^^^^^^

.. versionadded:: 2.8

Dumps a JSON representation for the Pootle database schema, currently only
MySQL, for debugging and comparison to a reference database schema.


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

    (env) $ pootle update_tmserver --dry-run
    (env) $ pootle update_tmserver --refresh --dry-run
    (env) $ pootle update_tmserver --rebuild --dry-run


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

    (env) $ pootle add_vfolders virtual_folders.json


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
revision counter to assist Pootle to determine how to handle subsequent uploads
of the file.

Available options:

.. django-admin-option:: --tmx

  .. versionadded:: 2.8.0

  Export every translation project as one zipped TMX file
  into :setting:`MEDIA_ROOT` directory.

.. django-admin-option:: --rotate

  .. versionadded:: 2.8.0

  Remove old exported zipped TMX files (except previous one)
  from :setting:`MEDIA_ROOT` directory after current exported file is saved.

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

  The database name or path to database file if you are using SQLite.

  Default for sqlite: ``dbs/pootle.db``.
  Default for mysql/postgresql: ``pootledb``.

.. django-admin-option:: --db-user

  .. versionadded:: 2.7.1

  Name of the database user. Not used with SQLite.

  Default: ``pootle``.

.. django-admin-option:: --db-host

  .. versionadded:: 2.7.1

  Database host to connect to. Not used with SQLite.

  Default: ``localhost``.

.. django-admin-option:: --db-port

  .. versionadded:: 2.7.1

  Port to connect to database on. Defaults to database backend's default port.
  Not used with SQLite.

.. django-admin-option:: --dev

  .. versionadded:: 2.8

  Creates a development configuration instead.

.. django-admin-option:: --yes

  .. versionadded:: 2.9

  Answer 'yes' to any questions blocking overwrite of existing config files.


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


.. _commands#pootle-project:

Pootle project tool
-------------------


.. django-admin:: project

project
^^^^^^^

To perform actions on projects we use multiple subcommands:

* :djadmin:`update` - Update one project from another one

Common options
^^^^^^^^^^^^^^

.. django-admin-option:: --source-project
.. django-admin-option:: --target-project
.. django-admin-option:: --language


Pootle project subcommands
^^^^^^^^^^^^^^^^^^^^^^^^^^


.. django-admin:: update

project update
++++++++++++++

.. versionadded:: 2.8.0


Update target project from source project:

* Add missing stores from source to target
* Remove stores missing in source from target
* Update stores from source project to corresponding stores in target project

.. code-block:: console

   (env) $ pootle project update --source-project=SRC_PROJECT --target-project=DEST_PROJECT

.. django-admin-option:: --translations

  Do not create missing stores and mark existing stores as obsoletes
  in the target project. Copy translations from source unit to target unit.
  Copy translations as suggestions for already translated units.


  .. code-block:: console

     (env) $ pootle project update --translations --source-project=SRC_PROJECT --target-project=DEST_PROJECT


.. _commands#pootle-fs:

Pootle FS
---------


.. django-admin:: fs

fs
^^

To interact with Pootle FS we use multiple subcommands:

* Admin:

  * :djadmin:`info` - Display filesystem info
  * :djadmin:`state` - Show current state

* Action:

  * :djadmin:`fetch` - Add a file from the filesystem to Pootle
  * :djadmin:`add` - Add a store from Pootle to the filesystem
  * :djadmin:`rm` - Remove a store and file from both Pootle and the filesystem
  * :djadmin:`resolve` - Handle conflicts in stores and files
  * :djadmin:`unstage` - Revert a staged action

* Execute:

  * :djadmin:`sync` - Execute staged actions


.. note:: The **action** staging commands require that you run
   :djadmin:`sync` in order to actually perform the staged actions.


.. _commands#pootle-fs-common-options:

Common options
^^^^^^^^^^^^^^

Pootle FS **action** and **execution** subcommands take the :option:`-p` and
:option:`-P` options which allow you to specify a glob to limit which files or
stores are affected by the command.

.. django-admin-option:: -p --fs-path

  Only affect files whose filesystem path matches a given glob.


  .. code-block:: console

     (env) $ pootle fs add --fs-path=MYPROJECT/af/directory/file.po MYPROJECT
     (env) $ pootle fs add --fs-path=MYPROJECT/af/* MYPROJECT
     (env) $ pootle fs add --fs-path=MYPROJECT/af/*/file.po MYPROJECT
     (env) $ pootle fs add --fs-path=MYPROJECT/af/directory/*.po MYPROJECT


  .. note:: The path should be relative to the Pootle FS URL setting for the
     project.


.. django-admin-option:: -P --pootle-path

  Only affect files whose Pootle path matches a given glob.

  .. code-block:: console

     (env) $ pootle fs add --pootle-path=/af/MYPROJECT/directory/file.po MYPROJECT
     (env) $ pootle fs add --pootle-path=/af/MYPROJECT/* MYPROJECT
     (env) $ pootle fs add --pootle-path=/af/MYPROJECT/*/file.po MYPROJECT
     (env) $ pootle fs add --pootle-path=/af/MYPROJECT/directory/*.po MYPROJECT


  .. note:: Keep in mind that Pootle paths always start with `/`.


.. _commands#pootle-fs-subcommands:

Pootle FS subcommands
^^^^^^^^^^^^^^^^^^^^^


.. django-admin:: add

fs add
++++++

.. versionadded:: 2.8.0


Stage for adding any new or changed stores from Pootle to the filesystem:

.. code-block:: console

   (env) $ pootle fs add MYPROJECT


This command is the functional opposite of the :djadmin:`fetch` command.

.. django-admin-option:: --force

  Conflicting files on the filesystem will be staged to be overwritten by the
  Pootle store.

  .. code-block:: console

     (env) $ pootle fs add --force MYPROJECT


.. django-admin:: fetch

fs fetch
++++++++

.. versionadded:: 2.8.0


Stage for fetching any new or changed files from the filesystem to Pootle:

.. code-block:: console

   (env) $ pootle fs fetch MYPROJECT


This command is the functional opposite of the :djadmin:`add` command.

.. django-admin-option:: --force

  Conflicting stores in Pootle to be overwritten with the filesystem file.

  .. code-block:: console

     (env) $ pootle fs fetch --force MYPROJECT


.. django-admin:: info

fs info
+++++++

.. versionadded:: 2.8.0

Retrieve the filesystem info for a project.

.. code-block:: console

   (env) $ pootle fs info MYPROJECT


.. django-admin:: resolve

fs resolve
++++++++++

.. versionadded:: 2.8.0

Stage for merging any stores/files that have either been updated both in Pootle
and filesystem.

When merging, if there are conflicts in any specific translation unit the
default behavior is to keep the filesystem version and convert the Pootle
version into a suggestion.  Suggestions can then we reviewed by translators to
ensure any corrections are correctly incorporated.

When there are no conflicts in unit :djadmin:`resolve` will handle the merge
without user input:

.. code-block:: console

   (env) $ pootle fs resolve MYPROJECT


.. django-admin-option:: --pootle-wins

  Alter the default conflict resolution of filesystem winning to instead use
  the Pootle version as the correct translation and converting the filesystem
  version into a suggestion.

  .. code-block:: console

    (env) $ pootle fs resolve --pootle-wins MYPROJECT

.. django-admin-option:: --overwrite

  Discard all translations.  Use only those translations from the filesytem,
  by default, or from Pootle if used together with :option:`--pootle-wins
  <resolve --pootle-wins>`

  .. code-block:: console

    (env) $ pootle fs resolve --overwrite MYPROJECT


.. django-admin:: rm

fs rm
+++++

.. versionadded:: 2.8.0

Remove any matched:

- Store that do not have a corresponding file in filesystem.
- File that do not have a corresponding store in Pootle.

.. code-block:: console

   (env) $ pootle fs rm MYPROJECT


.. django-admin-option:: --force

  Stage for removal conflicting/untracked files and/or stores.

  .. code-block:: console

    (env) $ pootle fs rm --force MYPROJECT


.. django-admin:: state

fs state
++++++++

.. versionadded:: 2.8.0

List the status of stores in Pootle and files on the filesystem.

.. code-block:: console

   (env) $ pootle fs state MYPROJECT


.. django-admin-option:: -t --type

  Restrict to specified :ref:`Pootle FS status <pootle_fs_statuses>`.

  .. code-block:: console

     (env) $ pootle fs state -t pootle_staged MYPROJECT


.. django-admin:: sync

fs sync
+++++++

.. versionadded:: 2.8.0

Commit any staged changes, effectively synchronizing the filesystem and Pootle.
This command is run after other Pootle FS commands have been used to stage
changes.

.. code-block:: console

   (env) $ pootle fs sync MYPROJECT


.. django-admin:: unstage

fs unstage
++++++++++

.. versionadded:: 2.8.0

Unstage any staged Pootle FS actions. This allows you to remove any staged
actions which you might have added erroneously.

.. code-block:: console

   (env) $ pootle fs unstage MYPROJECT


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

    (env) $ pootle find_duplicate_emails


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

    (env) $ pootle merge_user src_username target_username


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

    (env) $ pootle purge_user username [username ...]


.. django-admin:: update_user_email

update_user_email
^^^^^^^^^^^^^^^^^

.. versionadded:: 2.7.1


.. code-block:: console

    (env) $ pootle update_user_email username email

This command can be used if you wish to update a user's email address. This
might be useful if you have users with duplicate email addresses.

This command requires a mandatory ``username``, which should be a valid
username for a user of your site, and a mandatory valid ``email`` address.

.. code-block:: console

    (env) $ pootle update_user_email username email


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

    (env) $ pootle verify_user username [username ...]

Available options:

.. django-admin-option:: --all

  Verify all users of the site


.. _commands#running:

Running WSGI servers
--------------------

There are multiple ways to run Pootle, and some of them rely on running WSGI
servers that can be reverse proxied to a proper HTTP web server such as Nginx
or :ighttpd.

There are many more options such as `uWSGI
<https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html>`_, `Gunicorn
<http://gunicorn.org/>`_, etc.


.. _commands#deprecated:

Deprecated commands
-------------------

The following are commands that have been removed or deprecated:


.. django-admin:: refresh_stats

refresh_stats
^^^^^^^^^^^^^

.. removed:: 2.8

With the new stats infrastructure this is not needed anymore.


.. django-admin:: clear_stats

clear_stats
^^^^^^^^^^^

.. removed:: 2.8

With the new stats infrastructure this is not needed anymore.


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
:djadmin:`calculate_checks` command daily at 02:00 AM::

    00 02 * * * www-data source /var/www/sites/pootle/env/bin/activate; pootle calculate_checks

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

.. _django-assets: https://django-assets.readthedocs.io/en/latest/

.. _webassets: http://elsdoerfer.name/docs/webassets/
