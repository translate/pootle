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

``refresh_stats`` will do the following tasks:

- Update the statistics cache (this only useful if you are using memcached).

- Calculate quality checks so that they appear on the expanded overview page
  without a delay.

- Update :doc:`full text search index <indexing>` (Lucene or Xapian).


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

.. versionadded:: 2.5

With the ``--modified-since`` option it is possible to give a change identifier
(from the output of :ref:`commands#latest_change_id`) to specifically indicate
which changes need to be synced to disk. This will override Pootle on what
has/hasn't been synced to disk, and specifically those changes will be synced.
Note that bulk changes (from uploads and version control actions) don't yet
record fine-grained changes, and these will therefore not be synced to disk.
However, these should already be on disk, since those actions always sync to
disk anyway.


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

``update_stores`` has an extra command line option ``--keep`` that will
prevent it from overwriting any existing translation in the database, thus
only updating new translations, removing obsolete strings and discovering
new files and strings.

.. versionchanged:: 2.5.1

Note that ``--keep`` doesn't keep obsolete units around anymore, they are
either deleted in case the string is untranslated or marked as obsolete in
case the string was translated.

.. versionchanged:: 2.5

Along with ``--keep``, the ``--modified-since`` option can be used to
control the set of translations that will be updated: translations with a
change ID **greater than** the given value will be kept.

To illustrate the results of these two options, the following table
emulates the behavior of a ``pootle update_stores --modified-since=5
--keep`` run:

========================================== ============= =================
 File on disk                               DB before     DB after
                                            (change ID)   (result)
========================================== ============= =================
 New string appeared in existing file       <none>        String added
 Existing string changed in existing file   <none>        String updated
 Existing string changed in existing file   2             String updated
 Existing string changed in existing file   5             String updated
 Existing string changed in existing file   8             String kept
 New string in a new file                   <none>        String added
 String removed from the file               3             String removed
 String removed from the file               10            String removed
 File removed                               4             Strings removed
 File removed                               12            Strings removed
========================================== ============= =================


By default, ``update_stores`` will only update files that appear to have changed
on disk since the last synchronization with Pootle. To force all files to
update, specify ``--force``.

.. warning:: If files on the file system are corrupt, translations might be
   deleted from the database. Handle with care!


.. _commands#update_against_templates:

update_against_templates
^^^^^^^^^^^^^^^^^^^^^^^^

.. versionchanged:: 2.5

  The name of the command has been renamed from ``update_from_templates``.

Updates languages to match what is present in the translation templates.

This command is essentially an interface to the
Translate Toolkit command :ref:`pot2po <toolkit:pot2po>` with special Pootle
specific routines to update the database and file system to reflect the
latest version of translation templates for each language in a project.

During the process, translations existing in the database will first be synced
to disk (only in bilingual formats), then they will be updated against the
latest templates and after that the database will also be updated to reflect
the latest changes.

When updating existing translated files under a given language, the command
will retain any existing translations, fuzzy matching is performed on strings
with minor changes, and unused translations will be marked as obsolete. New
template files will initialize new untranslated files.

It is unlikely you will ever need to run this command for all projects at once.
Use the ``--directory``, ``--project`` or ``--language`` command line options
to be specific about the project, language or project/language pair you want to
target.

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

.. versionadded:: 2.5

This command updates the specified files from their :doc:`Version Control
System(s) <../features/version_control>`. It supports the ``--directory``,
``--project``, and ``--language`` parameters.

Pootle will take care to avoid version control conflicts, and will handle any
conflicts on a string level, just like it would if the update was done through
the web front-end.

The command first syncs database contents to disk.


.. _commands#commit_to_vcs:

commit_to_vcs
^^^^^^^^^^^^^

.. versionadded:: 2.5

This command commits the specified files to their :doc:`Version Control
System(s) <../features/version_control>`. It supports the ``--directory``,
``--project``, and ``--language`` parameters.

A file needs to be up to date, otherwise the commit will fail. Files can be
updated inside Pootle, or using the :ref:`commands#update_from_vcs` command.
This is not done automatically, otherwise the merged version of the file will
be committed without review without anybody knowing.


.. _commands#list_languages:

list_languages
^^^^^^^^^^^^^^

.. versionadded:: 2.5

This command prints all the language codes on the server. This might be useful
for automation.

Accepts the ``--modified-since`` parameter to list only those languages
modified since the change id given by :ref:`commands#latest_change_id`.

The option ``--project`` limits the output to one or more projects. Specify the
option multiple times for more than one project.


.. _commands#list_projects:

list_projects
^^^^^^^^^^^^^

.. versionadded:: 2.5

This command prints all the project codes on the server. This might be useful
for automation.

Accepts the ``--modified-since`` parameter to list only those projects
modified since the change id given by :ref:`commands#latest_change_id`.


.. _commands#latest_change_id:

latest_change_id
^^^^^^^^^^^^^^^^

.. versionadded:: 2.5

This command prints the ID of the latest change (submission) made on the
server. This is mostly useful in combination with other commands that operate
with these IDs.


.. _commands#assign-permissions:

assign_permissions
^^^^^^^^^^^^^^^^^^

.. versionadded:: 2.5.2

This command allows to assign permissions for a given user in a project,
language or translation project.

This command has two mandatory options: :option:`--permissions` and
:option:`--user`. It is also mandatory to either provide :option:`--language`
or :option:`--project`.

It is possible to provide both :option:`--language` and :option:`--project` at
the same time to indicate that the permissions should be applied only for a
given project inside a given language (i.e. for a given translation project).

+---------------------------+-------------------------------+
| Option                    | Accepted value                |
+===========================+===============================+
| :option:`--user`          | Valid username                |
+---------------------------+-------------------------------+
| :option:`--language`      | Valid language code           |
+---------------------------+-------------------------------+
| :option:`--project`       | Valid project code            |
+---------------------------+-------------------------------+
| :option:`--permissions`   | Comma separated list of valid |
|                           | permission codenames          |
+---------------------------+-------------------------------+

Check the list of :ref:`available permissions
<permissions#available_permissions>` to know which permissions you can use.

.. note:: All of the options, including :option:`--language`, can only be
   provided once, and all of them accept only one value.


The following example assigns the ``review``, ``view``, ``translate`` and
``suggest`` permissions to the ``sauron`` user in the ``task-123`` project for
the language ``de_AT``.

.. code-block:: bash

    $ pootle assign_permissions --user=sauron --language=de_AT --project=task-123 --permissions=review,view,translate,suggest


The following example assigns the ``translate`` permission to the ``sauron``
user in the ``task-123`` project.

.. code-block:: bash

    $ pootle assign_permissions --user=sauron --project=task-123 --permissions=translate


.. _commands#goals:

Goals
-----

These commands allow you to perform tasks with goals from the command line.


.. _commands#add-project-goals:

add_project_goals
^^^^^^^^^^^^^^^^^

This command allows you to create **project goals** for a given project reading
them from a phaselist file.

Such file has several lines where each line consists on two fields separated by
a tab. The first field specifies a goal name and the second one is the path of
a file:

.. code-block:: ini

    user1	./browser/branding/official/brand.dtd.pot
    other	./browser/chrome/browser/aboutCertError.dtd.pot
    user1	browser/chrome/browser/aboutDialog.dtd.pot
    user2	browser/chrome/browser/aboutSessionRestore.dtd.pot
    developer	./browser/chrome/browser/devtools/appcacheutils.properties.pot
    developer	browser/chrome/browser/devtools/debugger.dtd.pot
    user2	browser/chrome/browser/downloads/downloads.dtd.pot
    user3	browser/chrome/browser/engineManager.dtd.pot
    install	browser/chrome/browser/migration/migration.dtd.pot
    install	./browser/chrome/browser/migration/migration.properties.pot

The goals are created if necessary. If the goal exists and has any relationship
to any store, that relationships are deleted to make sure that the goals
specified on the phaselist file are only applied to the specified stores.

After all goals are created then they are tied to the files on template
translation project for the project as they are specified on the phaselist
file. If any specified file does not exist for the template translation project
on the given project then it is skipped.

This command has two mandatory options: :option:`--project` and
:option:`--filename`.

.. code-block:: bash

    $ pootle add_project_goals --project=tutorial --filename=phaselist.txt


.. _commands#manually_installing_pootle:

Manually Installing Pootle
--------------------------

These commands expose the database installation and upgrade process from the
command line.


.. _commands#setup:

setup
^^^^^

.. versionadded:: 2.5.1

This command either initializes a new DB or upgrades an existing DB, as
required.


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

.. _commands#updatedb:


updatedb
^^^^^^^^

.. versionchanged:: 2.5.1

This is a command line interface to Pootle's database schema upgrade
process.

This will only perform schema upgrades to version 2.5 from Pootle versions
older than 2.5. To upgrade to version 2.5.1 and later South's
:ref:`migrate command <south:commands>` must be used, after upgrading
to version 2.5.

For detailed instructions on upgrading, read the :ref:`upgrading` section
of the documentation.


.. _commands#upgrade:

upgrade
^^^^^^^^

.. versionadded:: 2.5.1

Performs post schema upgrade actions that are necessary to leave all the
bits in place. It also serves as a trigger for any changes needed by
Translate Toolkit version upgrades.

Optionally, the command accepts the ``--calculate-stats`` flag, which will
calculate full translation statistics after doing the upgrade.

Also, the ``--flush-checks`` flag forces flushing the existing quality
checks. This is useful when new quality checks have been added or existing
ones have been updated, but take into account that **this operation is
very expensive**.

For detailed instructions on upgrading, read the :ref:`upgrading` section
of the documentation.


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
