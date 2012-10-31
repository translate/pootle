.. _commands:

Management commands
===================

The *manage.py* commands are administration commands provided by Django,
Pootle or any external Django app being used with Pootle. How you run manage
commands depends on how you installed Pootle.


.. _commands#running_from_checkout:

Running from checkout
---------------------

If you run Pootle from a checkout (either directly from the
`Pootle repository <https://github.com/translate/pootle>`_ or from a
release tarball) you can use the *manage.py* file found in the main Pootle
directory *{checkout}/pootle*.

For example, to get information about all available manage.py commands, run::

    # ./manage.py help


.. _commands#running_from_install:

Running from install
--------------------

If you run Pootle from an install (with *setup.py* or your operating system
package) you will have to use the `django-admin` or `django-admin.py`
command that comes with Django.

Here is the same example::

    # django-admin.py help --settings=pootle.settings

Note since `django-admin.py` is a global command it needs to know where to
find Pootle via the ``--settings=pootle.settings`` command line option.


.. _commands#running:

Running WSGI servers
--------------------

There are multiple ways to run Pootle, and some of they rely on running WSGI
servers that can be reverse proxyed to a proper HTTP web server such as nginx
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
expects a path relative to the *po/* directory to limit it's action to.

.. versionchanged:: 2.1.2

The commands target can be limited in a more flexible way using the ``--project``
``--language`` command line options. They can be repeated to indicate multiple
languages or projects. If you use both options together it will only match the
files that match both languages and projects selected.

If you need to limit the commands to certain files or subdirectories you can
use the ``--path-prefix`` option, path should be relative to project/language
pair.

For example, to *refresh_stats* for the tutorial project only, run::

    ./manage.py refresh_stats --project=tutorial

To only refresh a the Zulu and Basque language files within the tutorial
project, run::

    ./manage.py refresh_stats --project=tutorial --language=zu --language=eu


.. _commands#refresh_stats:

refresh_stats
^^^^^^^^^^^^^

This command will go through all existing projects making sure calculated data
is up to date. Running *refresh_stats* immediately after an install, upgrade
or after adding a large number of files will make Pootle feel faster as it will
require less on-demand calculation of expensive statistics.

*refresh_stats* will do the following tasks:

- Update the statistics cache (this only useful if you are using memcached).

- Calculate quality checks so that they appear on the expanded overview page
  without a delay.

- Update :doc:`full text search index <indexing>` (Lucene or Xapian).


.. _commands#sync_stores:

sync_stores
^^^^^^^^^^^

This command will save all translations currently in the database to the file
system, thereby bringing the files under the *po/* directory in sync with the
Pootle database.

.. note:: For better performance Pootle keeps translations in database and
   doesn't save them to disk except on demand (before file downloads and
   before major file level operations like version control update).

You must run this command before taking backups or running scripts that modify
the translation files directly on the file system, otherwise you might miss out
on translations that are in database but not yet saved to disk.


.. _commands#update_stores:

update_stores
^^^^^^^^^^^^^

This command is the opposite of :ref:`commands#sync_stores`. It will update the
strings in database to reflect what is on disk, as Pootle will not detect
changes in the file system on it's own.

It will also discover and import any new files added to existing languages
within the projects.

You must run this command after running scripts that modify translation files
directly on the file system.

*update_stores* has an extra command line option ``--keep`` that will prevent
it from overwriting any existing translation in the database, thus only
updating new translations and discovering new files and strings.

By default *update_stores* will only update files that appear to have changed
on disk since the last synchronization with Pootle. To force all files to
update, specify ``--force``.

.. warning:: If files on the file system are corrupt, translations might be
   deleted from the database. Handle with care!


.. _commands#update_from_templates:

update_from_templates
^^^^^^^^^^^^^^^^^^^^^

This updates languages to match what is present in the translation templates.
This command is essentially an interface to the
Translate Toolkit command :ref:`pot2po <toolkit:pot2po>` with special Pootle
specific routines to update the database and file system to reflect the
latest version of translation templates for each language in a project.

When updating existing translated files under a given language the command
will retain any existing translations, fuzzy matching is performed on strings
with minor changes, unused translations will be marked as obsolete. New
template files will initialize new untranslated files.

It is unlikely you will ever need to run this command for all projects at once.
Use the ``--directory`` command line option to be specific about the project or
project/language pair you want to target.

.. warning:: If the template files are corrupt translations might be lost.
   If you generate templates based on a script make sure they are in good
   shape.


.. _commands#update_translation_projects:

update_translation_projects
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This command scans project directories looking for files matching languages not
added to the project then adds them. It basically repeats the discovery process
done by Pootle when you create a new project.

Using the ``--cleanup`` command line option, languages added to projects that
no longer have matching files on the filesystem will be deleted.


.. _commands#update_from_vcs:

update_from_vcs
^^^^^^^^^^^^^^^

.. versionadded:: 2.2

This command updates the specified files from their :doc:`Version Control
System(s) <../features/version_control>`. It supports the parameters
``--directory``, ``--project``, and ``--language``.

Pootle will take care to avoid version control conflicts, and will handle any
conflicts on a string level, just like it would if the update was done through
the web front-end.


.. _commands#commit_to_vcs:

commit_to_vcs
^^^^^^^^^^^^^

.. versionadded:: 2.2

This command commits the specified files to their :doc:`Version Control
System(s) <../features/version_control>`. It supports the parameters
``--directory``, ``--project``, and ``--language``.

A file needs to be up to date, otherwise the commit will fail. Files can be
updated inside Pootle, or using the :ref:`commands#update_from_vcs` command.
This is not done automatically, otherwise the merged version of the file will
be committed without review without anybody knowing.


.. _commands#list_languages:

list_languages
^^^^^^^^^^^^^^

.. versionadded:: 2.2

This command prints all the language codes on the server. This might be useful
for automation.


.. _commands#list_projects:

list_projects
^^^^^^^^^^^^^

.. versionadded:: 2.2

This command prints all the project codes on the server. This might be useful
for automation.


.. _commands#latest_change_id:

latest_change_id
^^^^^^^^^^^^^^^^

.. versionadded:: 2.2

This command prints the ID of the latest change (submission) made on the
server. This is mostly useful in combination with other commands that operate
with these IDs.


.. _commands#manually_installing_pootle:

Manually installing Pootle
--------------------------

These commands expose the database installation and upgrade process from the
command line.


.. _commands#syncdb:

syncdb
^^^^^^

Strictly speaking *syncdb* is a generic django *manage.py* command that creates
empty database tables. It has been customized for Pootle to create everything
required for a bare bones install. This includes database tables, default
permissions, some default objects used internally by Pootle (like the "default"
and "nobody" user profiles) and the special Terminology and :ref:`Templates
languages <templates#the_templates_language>`.

If you just run *syncdb* you will have a usable Pootle install but you will
need to create all languages manually, and you will not have a tutorial project
to play with.

Use this command if you plan to upgrade from a Pootle 1.2 install or if you
don't like having many languages by default.


.. _commands#initdb:

initdb
^^^^^^

This is Pootle's install process, it creates the default admin user, populates
the language table with several languages with their correct fields,
initializes several terminology projects, and creates the tutorial project.

*initdb* can only be run after *syncdb*.

.. note:: *initdb* will not import translations into the database, so the first
   visit to Pootle after *initdb* will be very slow. **It is best to run
   refresh_stats immediately after initdb**.


.. _commands#updatedb:

updatedb
^^^^^^^^

This is a command line interface to Pootle's database scheme upgrade process.
A database upgrade is usually triggered automatically on the first visit to a
:doc:`new version of Pootle <upgrading>`, but for very large installs database
upgrades can be too slow for the browser and it is best to run *updatedb*
from the command line.


.. _commands#useful_django_commands:

Useful Django commands
----------------------


.. _commands#changepassword:

changepassword
^^^^^^^^^^^^^^

::

    ./manage.py changepassword <username>

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

Running commands in cron
------------------------

If you want to schedule certain actions on your Pootle server, using
management commands with cron might be a solution.

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
