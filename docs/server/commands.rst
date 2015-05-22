.. _commands:

Management commands
===================

The management commands are administration commands provided by Django, Pootle
or any external Django app being used with Pootle. You will usually run these
commands by issuing ``pootle <command> [options]``.

For example, to get information about all available management commands, you
will run:

.. code-block:: bash

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

The commands target can be limited in a more flexible way using the ``--project``
``--language`` command line options. They can be repeated to indicate multiple
languages or projects. If you use both options together it will only match the
files that match both languages and projects selected.

For example, to *refresh_stats* for the tutorial project only, run:

.. code-block:: bash

    $ pootle refresh_stats --project=tutorial

To only refresh a the Zulu and Basque language files within the tutorial
project, run:

.. code-block:: bash

    $ pootle refresh_stats --project=tutorial --language=zu --language=eu


.. pootle_command:: refresh_stats

refresh_stats
^^^^^^^^^^^^^

Refreshes all calculated statistics ensuring that they are up-to-date.

The refreshing of the statistics is done by a background job so that it doesn't
impact the normal operation of the server.  It will flush existing cached
statistics data and update the statistics cache.

.. note:: Disabled projects are processed.

.. warning:: Do not run this command if you have multiple workers running
   simultaneously. It should be run with a single worker process only.

It's necessary to run this command after installing or upgrading Pootle. Also
consider running this command when things might go out-of-sync: if you make
changes directly in the database, if the cache backend has been restarted, etc.

The time it takes to complete the whole process will vary depending on the
number of translations you have in the database. If a user hits a page that
needs to display stats but they haven't been calculated yet, a message will be
displayed indicating that the stats are being recalculated.

The ``--calculate-checks`` option ensures that all quality checks are
recalculated for all existing units in the database.

To only recalculate the ``date_format`` quality check, run:

.. code-block:: bash

    $ pootle refresh_stats --calculate-checks --check=date_format

When the ``--calculate-wordcount`` option is set, the source wordcount
will be recalculated for all existing units in the database.


.. pootle_command:: refresh_stats_rq

refresh_stats_rq
^^^^^^^^^^^^^^^^

.. versionadded:: 2.7

Refreshes all calculated statistics ensuring that they are up-to-date.

A background process will create a task for every file to make sure calculated
statistics data is up to date. When the task for a file completes then further
tasks will be created for the files parents.

.. note:: Files in disabled projects are processed.

.. note:: :pc:`refresh_stats` (the old command which works with a single
   worker) is roughly twice as fast compared to this version of the command.
   Your mileage might vary.

This command was added to allow statistics to be updated when using multiple
RQ workers.


.. pootle_command:: retry_failed_jobs

retry_failed_jobs
^^^^^^^^^^^^^^^^^

.. versionadded:: 2.7

Requeue failed RQ jobs.

Backgorund RQ jobs can fail for various reasons.  To push them back into the
queue you can run this command.

Examine the RQ worker logs for tracebacks before trying to requeue your jobs.


.. pootle_command:: calculate_checks

calculate_checks
^^^^^^^^^^^^^^^^

.. versionadded:: 2.7

This command will create a background job to go through all units and
recalculate quality checks.

.. note:: Disabled projects are processed.

:pc:`calculate_checks` will flush existing caches and update the quality
checks cache.

It's necessary to run this command after upgrading Pootle if new quality
checks are added.

The time it takes to complete the whole process will vary depending on the
number of units you have in the database. If a user hits a page that needs to
display stats but they haven't been calculated yet, then a message will be
displayed indicating that the stats being calculated.

Use the ``--check`` option to force calculaton of a specified check.  To
recalculate only the ``date_format`` quality checks, run:

.. code-block:: bash

    $ pootle calculate_checks --check=date_format


.. pootle_command:: refresh_scores

refresh_scores
^^^^^^^^^^^^^^

.. versionadded:: 2.7

Recalculates the scores for all users.

When the ``--reset`` option is used , all score log data is removed and `zero`
score is set for all users.


.. pootle_command:: sync_stores

sync_stores
^^^^^^^^^^^

.. versionchanged:: 2.7

Save all translations currently in the database to the file system, thereby
bringing the files under the :setting:`PODIRECTORY` directory in sync with the
Pootle database.

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

The default behavior of :pc:`sync_stores` can be altered by specifying these
parameters:

``--force``
  Synchronizes files even if nothing changed in the database.

``--overwrite``
  Copies all units from database stores regardless if they have been
  modified since the last sync or not. This operation will (over)write
  existing on-disk files.

``--skip-missing``
  Ignores files missing on disk, and no new files will be created.


.. pootle_command:: update_stores

update_stores
^^^^^^^^^^^^^

This command is the opposite of :pc:`sync_stores`. It will update the strings
in the database to reflect what is on disk, as Pootle will not detect changes
in the file system on its own.

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

``update_stores`` accepts several parameters:

``--force``
  Updates in-DB translations even if the on-disk file hasn't been changed
  since the last sync operation.

``--overwrite``
  Mirrors the on-disk contents of the file. If there have been changes in
  the database **since the last sync operation**, these will be
  overwritten.

.. warning:: If files on the file system are corrupt, translations might be
   deleted from the database. Handle with care!


.. pootle_command:: list_languages

list_languages
^^^^^^^^^^^^^^

Lists all the language codes for languages hosted on the server. This can be
useful for automation.


.. pootle_command:: list_projects

list_projects
^^^^^^^^^^^^^

Lists all the project codes on the server. This might can be useful for
automation.


.. pootle_command:: revision

revision
^^^^^^^^

.. versionadded:: 2.7

Print the latest revision number.

The revision is a common system-wide counter for units. It is incremented with
every translation action made from the browser. Zero length units that have
been auto-translated also increment the unit revision.

The revision counter is stored in the database but also in cache for faster
retrieval. If for some reason the revision counter was removed or got
corrupted, passing the ``--restore`` flag to the command will restore the
counter's value based on the revision data available on the relational DB
backend. You shouldn't need to ever run this, but if for instance you deleted
your cache you will need to restore the counter to ensure correct operation.


.. pootle_command:: changed_languages

changed_languages
^^^^^^^^^^^^^^^^^

.. versionadded:: 2.7

Produces a comma-separated list of language codes that changed since the last
sync operation.

When ``--after-revision`` is specified with a revision number as an argument,
it will print the language codes for languages that have changed since the
specified revision.


.. pootle_command:: test_checks

test_checks
^^^^^^^^^^^

Tests any given string pair or unit against all or certain checks from the
command line. This is useful for debugging and developing new checks.

String pairs can be specified by setting the values to be checked in the
``--source=<"source_text">`` and ``--target="<target_text>"`` command-line
arguments.

Alternatively, ``--unit=<unit_id>`` can be used to reference an existing
unit from the database.

By default, :pc:`test_checks` tests all existing checks. When
``--check=<checkname>`` is set, only specific checks will be tested against.


.. pootle_command:: regenerate-checks-descriptions

regenerate_checks_descriptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 2.7

Regenerates the quality checks descriptions page.

If new checks are added, or existing checks are updated or removed you should
run this command in order to update the check descriptions.


.. _commands#translation-memory:

Translation Memory
------------------

These commands allow you to setup and manage :doc:`Translation Memory
</features/translation_memory>`.

.. pootle_command:: update_tmserver

update_tmserver
^^^^^^^^^^^^^^^

.. versionadded:: 2.7

Updates the ``default`` server in :setting:`POOTLE_TM_SERVER`.  The command
reads translations from the current Pootle install and builds the TM resources
in the TM server.

By default the command will only add new translations to the server.  To
rebuild the server from scratch use :option:`--rebuild`, this will completely
remove the TM and rebuild it.  To ensure that the TM server remains available
when you rebuild you can add :option:`--overwrite`.

To see how many units will be loaded into the server use :option:`--dry-run`,
no actual data will be loaded.

.. _commands#vfolders:

Virtual Folders
---------------

These commands allow you to perform tasks with virtual folders from the command
line.


.. pootle_command:: add_vfolders

add_vfolders
^^^^^^^^^^^^

.. versionadded:: 2.7

This command allows you to create :ref:`virtual folders <virtual_folders>` from
a JSON file. If the specified virtual folders already exist then they are
updated with the provided data, but only if the data differs.

Check the specs for the :ref:`JSON format <virtual_folders#json-format>` in
order to know how to craft a JSON file that fits your needs.

This command requires a mandatory filename argument.

.. code-block:: bash

    $ pootle add_vfolders virtual_folders.json


.. _commands#manually_installing_pootle:

Manually Installing Pootle
--------------------------

These commands expose the database installation and upgrade process from the
command line.


.. _commands#migrate:

migrate
^^^^^^^

.. versionchanged:: 2.7


.. note::

  Since the addition of the :command:`setup` management command it is not
  necessary to directly run this command. Please refer to the :ref:`Upgrading
  <upgrading>` or :ref:`Installation <installation>` instructions to see how to
  run the :command:`setup` management command in those scenarios.


This is Django's :djadmin:`django:migrate` command, which syncs the state
of models with the DB and applies migrations for them.


.. pootle_command:: initdb

initdb
^^^^^^

Initialises a new Pootle install.

This is part an optional part of Pootle's install process, it creates the
default *admin* user, populates the language table with several languages with
their correct fields, initializes several terminology projects, and creates the
tutorial project.

:pc:`initdb` can only be run after :ref:`commands#migrate`.

.. note:: :pc:`initdb` will not import translations into the database, so the
  first visit to Pootle after :pc:`initdb` will be very slow. **It is best to
  run** :pc:`refresh_stats` **immediately after initdb**.


.. _commands#collectstatic:

collectstatic
^^^^^^^^^^^^^

Running the Django admin :djadmin:`django:collectstatic` command finds
and extracts static content such as images, CSS and JavaScript files used by 
the Pootle server, so that they can be served separately from a static
webserver.  Typically, this is run with the :option:`--clear`
:option:`--noinput` options, to flush any existing static data and use default
answers for the content finders.


.. _commands#assets:

assets
^^^^^^

Pootle uses the Django app `django-assets`_ interface of `webassets` to minify
and bundle CSS and JavaScript; this app has a management command that is used
to make these preparations using the command ``assets build``. This command is
usually executed after the :ref:`collectstatic <commands#collectstatic>` one.


.. pootle_command:: webpack

webpack
^^^^^^^

.. versionadded:: 2.7

The `webpack <http://webpack.github.io/>`_ tool is used under the hood to
bundle JavaScript scripts, and this management command is a convenient
wrapper that sets everything up ready for production and makes sure to
include any 3rd party customizations.

When the ``--dev`` flag is enabled, development builds will be created and
the process will start a watchdog to track any client-side scripts for
changes. Use this only when developing Pootle.


.. _commands#running:

Running WSGI servers
--------------------

There are multiple ways to run Pootle, and some of them rely on running WSGI
servers that can be reverse proxied to a proper HTTP web server such as nginx
or lighttpd.

The Translate Toolkit offers a bundled CherryPy server but there are many more
options such as gunicorn, flup, paste, etc.


.. pootle_command:: run_cherrypy

run_cherrypy
^^^^^^^^^^^^

Run the CherryPy server bundled with the Translate Toolkit.

Available options:

``--host``
  The hostname to listen on.

  Default: ``127.0.0.1``.

``--port``
  The TCP port on which the server should listen for new connections.

  Default: ``8080``.

``--threads``
  The number of working threads to create.

  Default: ``1``.

``--name``
  The name of the worker process.

  Default: :func:`socket.gethostname`.

``--queue``
  Specifies the maximum number of queued connections. This is the the
  ``backlog`` argument to :func:`socket.listen`.

  Default: ``5``.

``--ssl_certificate``
  The filename of the server SSL certificate.

``--ssl_privatekey``
  The filename of the server's private key file.


.. _commands#running_in_cron:

Running Commands in cron
------------------------

If you want to schedule certain actions on your Pootle server, using management
commands with cron might be a solution.

The management commands can perform certain batch commands which you might want
to have executed periodically without user intervention.

For the full details on how to configure cron, read your platform documentation
(for example ``man crontab``). Here is an example that runs the
:pc:`refresh_stats` command daily at 02:00 AM::

    00 02 * * * www-data /var/www/sites/pootle/manage.py refresh_stats

Test your command with the parameters you want from the command line. Insert it
in the cron table, and ensure that it is executed as the correct user (the same
as your web server) like *www-data*, for example. The user executing the
command is specified in the sixth column. Cron might report errors through
local mail, but it might also be useful to look at the logs in
*/var/log/cron/*, for example.

If you are running Pootle from a virtualenv, or if you set any custom
``PYTHONPATH`` or similar, you might need to run your management command from a
bash script that creates the correct environment for your command to run from.
Call this script then from cron. It shouldn't be necessary to specify the
settings file for Pootle — it should automatically be detected.

.. _django-assets: http://elsdoerfer.name/docs/django-assets/

.. _webassets: http://elsdoerfer.name/docs/webassets/
