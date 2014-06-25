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


.. _commands#running:

Running WSGI servers
--------------------

There are multiple ways to run Pootle, and some of them rely on running WSGI
servers that can be reverse proxied to a proper HTTP web server such as nginx
or lighttpd.

The Translate Toolkit offers a bundled CherryPy server but there are many more
options such as gunicorn, flup, paste, etc.


.. _commands#run_cherrypy:

run_cherrypy
^^^^^^^^^^^^

.. versionadded:: 2.5

This command runs the CherryPy server bundled with the Translate Toolkit.

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


.. _commands#managing_pootle_projects:

Managing Pootle projects
------------------------

These commands will go through all existing projects performing maintenance
tasks. The tasks are all available through the web interface but on a project
by project or file by file basis.

All commands in this category accept a ``--directory`` command line option that
limits its action to a path relative to the *po/* directory.

.. versionchanged:: 2.1.2

The commands target can be limited in a more flexible way using the ``--project``
``--language`` command line options. They can be repeated to indicate multiple
languages or projects. If you use both options together it will only match the
files that match both languages and projects selected.

If you need to limit the commands to certain files or subdirectories you can
use the ``--path-prefix`` option, path should be relative to project/language
pair.

For example, to *refresh_stats* for the tutorial project only, run:

.. code-block:: bash

    $ pootle refresh_stats --project=tutorial

To only refresh a the Zulu and Basque language files within the tutorial
project, run:

.. code-block:: bash

    $ pootle refresh_stats --project=tutorial --language=zu --language=eu


.. _commands#refresh_stats:

refresh_stats
^^^^^^^^^^^^^

This command will go through all existing projects making sure calculated data
is up to date. Running ``refresh_stats`` immediately after an install, upgrade
or after adding a large number of files will make Pootle feel faster as it will
require less on-demand calculation of expensive statistics.

``refresh_stats`` will flush existing caches and update the statistics cache.

When the ``--calculate-checks`` option is set, quality checks will be
recalculated for all existing units in the database.

To only recalculate date_format quality checks, run:

.. code-block:: bash

    $ pootle refresh_stats --calculate-checks --check=date_format

When the ``--calculate-wordcount`` option is set, source_wordcount will be
recalculated for all existing units in the database.


.. _commands#refresh_scores:

refresh_scores
^^^^^^^^^^^^^

This command will go through all users and recalculate user's score.

When the ``--reset`` option is set, all score log data is removed and
`zero` score is set for all users.


.. _commands#sync_stores:

sync_stores
^^^^^^^^^^^

This command will save all translations currently in the database to the file
system, thereby bringing the files under the :setting:`PODIRECTORY` directory
in sync with the Pootle database.

.. note:: For better performance Pootle keeps translations in database and
   doesn't save them to disk except on demand (before file downloads and
   major file level operations like version control updates).

You must run this command before taking backups or running scripts that modify
the translation files directly on the file system, otherwise you might miss out
on translations that are in database but not yet saved to disk.

When the ``--overwrite`` option is specified, the sync operation will not be
conservative and it will overwrite the existing files on disk, making strings
obsolete and updating the file's structure.

With the ``--skip-missing`` option, files that are missing on disk will be
ignored, and no new files will be created.

With the ``--force`` option, files that were synced after the last change in DB
won't be ignored.

.. _commands#update_stores:

update_stores
^^^^^^^^^^^^^

This command is the opposite of :ref:`commands#sync_stores`. It will update the
strings in database to reflect what is on disk, as Pootle will not detect
changes in the file system on its own.

It will also discover and import any new files added to existing languages
within the projects.

You must run this command after running scripts that modify translation files
directly on the file system.

``update_stores`` has an extra command line option ``--overwrite`` that will
overwrite any existing translation in the database, without this
option only updating new translations, removing obsolete strings and discovering
new files and strings will be done.

.. release::2014-06-23
``update_stores`` scans project directories looking for files matching languages not
added to the project then adds them. It basically repeats the discovery process
done by Pootle when you create a new project. Languages added to projects that
have no matching files on the filesystem will be disabled.

.. versionchanged:: 2.5.1

Note that ``update_stores`` doesn't keep obsolete units around anymore, they are
either deleted in case the string is untranslated or marked as obsolete in
case the string was translated.

.. versionchanged:: 2.5

By default, ``update_stores`` will only update files that appear to have changed
on disk since the last synchronization with Pootle. To force all files to
update, specify ``--force``.

.. warning:: If files on the file system are corrupt, translations might be
   deleted from the database. Handle with care!


.. _commands#list_languages:

list_languages
^^^^^^^^^^^^^^

.. versionadded:: 2.5

This command prints all the language codes on the server. This might be useful
for automation.


.. _commands#list_projects:

list_projects
^^^^^^^^^^^^^

.. versionadded:: 2.5

This command prints all the project codes on the server. This might be useful
for automation.


.. _commands#revision:

revision
^^^^^^^^

This command prints the number of the latest revision.


.. _commands#changed_languages:

changed_languages
^^^^^^^^^^^^^^^^^

Lists a comma-separated list of language codes that changed since the last
sync operation.

When ``--after-revision`` is specified with a revision number as an
argument, it will print the language codes that changed since the
specified revision.


.. _commands#test_checks:

test_checks
^^^^^^^^^^^

Tests any given string pair or unit against all or certain checks from the
command line. This is useful for debugging and developing new checks.

String pairs can be specified by setting the values to be checked in the
``--source=<"source_text">`` and ``--target="<target_text>"`` command-line
arguments.

Alternatively, ``--unit=<unit_id>`` can be used to reference an existing
unit from the database.

By default, :ref:`commands#test_checks` tests all existing checks. When
``--check=<checkname>`` is set, only specific checks will be tested
against.


.. _commands#manually_installing_pootle:

Manually Installing Pootle
--------------------------

These commands expose the database installation and upgrade process from the
command line.


.. _commands#syncdb:

syncdb
^^^^^^

Originally, ``syncdb`` was a generic Django management command that creates
empty database tables. It has been customized for Pootle to create everything
required for a bare bones install for releases up to 2.5.0. This includes
database tables, default permissions, some default objects used internally by
Pootle (like the *"default"* and *"nobody"* user profiles) and the special
:ref:`Terminology <terminology>` project and
:ref:`Templates language <templates#the_templates_language>`.

For releases up to 2.5.0, if you just run ``syncdb`` you will have a usable
Pootle install but you will need to create all languages manually, and you will
not have a tutorial project to play with.  For releases after 2.5.0, ``syncdb``
is not sufficient to create the database schema; it will remain incomplete and
unusable until you apply all migrations to the database schema by running the
:ref:`commands#migrate` command.


.. _commands#migrate:

migrate
^^^^^^^

.. versionadded:: 2.5.1


.. note::

  Since the addition of the :ref:`setup <commands#setup>` management command it
  is not necessary to directly run this command. Please refer to the
  :ref:`Upgrading <upgrading>` or :ref:`Installation <installation>`
  instructions to see how to run the ``setup`` management command in those
  scenarios.


This is South's :ref:`migrate command <south:commands>`, which applies
migrations to bring the database up to the latest schema revision. It is
required for releases after 2.5.0, even for a fresh install where you are not
upgrading from a previous release.


.. _commands#initdb:

initdb
^^^^^^

This is Pootle's install process, it creates the default *admin* user, populates
the language table with several languages with their correct fields, initializes
several terminology projects, and creates the tutorial project.

``initdb`` can only be run after :ref:`commands#syncdb` and :ref:`commands#migrate`.

.. note:: ``initdb`` will not import translations into the database, so the
  first visit to Pootle after ``initdb`` will be very slow. **It is
  best to run** :ref:`commands#refresh_stats` **immediately after initdb**.


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

.. _commands#useful_django_commands:

Useful Django commands
----------------------


.. _commands#changepassword:

changepassword
^^^^^^^^^^^^^^

.. code-block:: bash

    $ pootle changepassword <username>

This can be used to change the password of any user from the command line.


.. _commands#createsuperuser:

createsuperuser
^^^^^^^^^^^^^^^

This creates a new admin user. It will prompt for username, password and email
address.


.. _commands#dbshell:

dbshell
^^^^^^^

This opens a database command prompt with the Pootle database already loaded.
It is useful if you know SQL.

.. warning:: Try not to break anything.


.. _commands#shell:

shell
^^^^^

This opens a Python shell with the Django and Pootle environment already
loaded. Useful if you know a bit of Python or the Django models syntax.


.. _commands#running_in_cron:

Running Commands in cron
------------------------

If you want to schedule certain actions on your Pootle server, using management
commands with cron might be a solution.

The management commands can perform certain batch commands which you might want
to have executed periodically without user intervention.

For the full details on how to configure cron, read your platform documentation
(for example ``man crontab``). Here is an example that runs the
:ref:`commands#refresh_stats` command daily at 02:00 AM::

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
