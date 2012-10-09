.. _installation:

Installation
============

System requirements
-------------------

Your Pootle installation will need to be flexible enough to handle the
translation load.  The recommended hardware depends highly on the performance
you expect, the number of users you want to support, and the number and size of
the files you want to host.  If you want to host a lot of projects, e.g.
multiple translations of large projects such as OpenOffice.org, Mozilla
Firefox, GNOME or KDE we would recommend:

- At least 512MB RAM, but more will be highly beneficial

- :doc:`System optimization <optimization>`

But of course if you are simply hosting one language or a number of languages
for a small localization project with only a few files on the server then you
can use:

- 256 MB of RAM, unless your web server might demand more

- You will still benefit from the performance increase if you can
  :doc:`optimize <optimization>` your system.

Your disk space should always be enough to store your files and your Pootle
database, with some extra space available.

This guide describes how to install manually Pootle and its requirements in
your machine.  There are also available :doc:`ready-to-run packages
<ready-to-run_packages>` from BitNami.


.. _installation#software_requirements:

Software requirements
---------------------

This section helps you choose the versions of software that you need, the
dependencies and optional software.  These might be slightly different if you
are installing e.g. Windows so please familiarize yourself with your target
platform and installation options before downloading all the software.

.. note::

    Pootle will display warnings and suggestions about missing dependencies on
    the admin page.

For GNU/Linux users most of the required and optional dependencies are
available through the operating system's package manager or through Python's
standard package management command *easy_install*


.. _installation#prerequisite_software:

Prerequisite Software
^^^^^^^^^^^^^^^^^^^^^

==========================  =====================  ======================================================================  ================================================================
 Package                     Best version           Website                                                                 Notes
==========================  =====================  ======================================================================  ================================================================
 Pootle                      2.2 or later           http://sourceforge.net/projects/translate/files/Pootle/ 
 Django                      1.3 or later           https://www.djangoproject.com/download/
 Translate Toolkit           Latest version         http://sourceforge.net/projects/translate/files/Translate%20Toolkit/
 Python                      Latest 2.x version     http://www.python.org/                                                  At least version 2.4
 lxml                        2.1.4 or later         http://pypi.python.org/pypi/lxml/                                       XLIFF support and HTML sanitation and cleanup for news items
 Python database bindings                           See the `optional software`_ list below
 South                                              http://south.aeracode.org/  \\ pip install South                        Required for upgrading between Pootle versions
 django-voting                                      http://code.google.com/p/django-voting/ \\ pip install django-voting
 webassets                   0.6 or later           https://github.com/miracle2k/webassets/ \\ pip install webassets         For bundling assets.
 cssmin                                             https://github.com/zacharyvoase/cssmin \\ pip install cssmin             Required for webassets.
==========================  =====================  ======================================================================  ================================================================


.. _installation#optional_software:

Optional Software
^^^^^^^^^^^^^^^^^

================================  ==============  =====================================================================  ================================================================================================================
 Package                           Version         Website                                                                Reason                                                                                                           
================================  ==============  =====================================================================  ================================================================================================================
 MySQLdb                                           http://mysql-python.sourceforge.net/                                   MySQL support for django
 MySQL_ [#f1]_                     4.1 or later                                                                           Database for storing Users, Projects and Language information
 python-memcache and memcached                     http://www.tummy.com/Community/software/python-memcached/              more efficient caching
 :doc:`Apache <apache>`                                                                                                   Web server (best way to run Pootle)
 Xapian [#f2]_                                     http://xapian.org/docs/bindings/python/                                :doc:`Indexing <indexing>` library to speed up searching
 PyLucene                                          http://pylucene.osafoundation.org/                                     Indexing library to speed up searching
 zip and unzip                                                                                                            Fast (un)compression of file archives
 iso-codes                         any             http://packages.debian.org/unstable/source/iso-codes                   Enables translated language and country names
 python-levenshtein                                http://sourceforge.net/projects/translate/files/python-Levenshtein/    Provides speed-up when updating from templates
 python-ldap                                       http://www.python-ldap.org/                                            If using :ref:`LDAP <authentication#ldap>` authentication
 sqlite [#f3]_                     version 3       http://www.sqlite.org/                                                 Database for translation statistics in Pootle 2.0. Optionally the Django database, but this isn't recommended.
 Version Control Software                                                                                                 :ref:`Version control <version_control>` integration
================================  ==============  =====================================================================  ================================================================================================================

.. rubric:: Notes

.. [#f1] Django can use a number of database engines for it's backend database
  but we have only tested with MySQL and the default SQLite. You are strongly
  encouraged to use MySQL rather than SQLite for any non-trivial installation.

.. [#f2] Xapian versions before 1.0.13 are incompatible with Apache; Pootle
  will detect Xapian version and disable indexing when running under
  *mod_python* or *mod_wsgi* if needed.

  Checking for Xapian relies on the `xapian-check` command, which is found in
  the `xapian-tools` package in Debian-based systems.

.. [#f3] sqlite 3 support is built-in since Python 2.5, those using 2.4 will
  also need to install the `python-sqlite2` package.  Since Pootle 2.1 this is
  not required any more if using another database engine.


.. _installation#running_pootle:

Running Pootle
--------------

Pootle can be run directly from the directory of files. Although it can be
installed in your system via the *setup.py* command, such a system-wide
installation is never really required, and probably only relevant for
distribution packagers.

The recommended way to run Pootle is under a web server. This will provide the
best performance. The built-in web server is sufficient for the first
experiments, but ideally you should plan to have it running under a better
server eventually.

.. _installation#running_from_checkout_or_archive:

Running from checkout or archive
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Running from checkout is the easiest way to test Pootle, no need to install it
or even configure, just change your directory to inside Pootle's directory
(extracted from downloaded archive or checked out from Git), and then execute
``PootleServer``.

For example if you have downloaded `Pootle-2.1.1.tar.bz2
<http://sourceforge.net/projects/translate/files/Pootle/>`_ you would do::

    tar xvf Pootle-2.1.1.tar.bz2
    cd Pootle-2.1.1
    ./PootleServer

By default the Pootle server will listen on the 8080 port, and can be accessed
from your web browser at *http://localhost:8080/*.

On the very first request Pootle will take a few minutes to setup a Django
database under the *dbs/* subdirectory and will scan all the default projects
and translation files under the *po* directory. Finally, it will redirect to
the front page.


.. _installation#installing_pootle:

Installing Pootle
^^^^^^^^^^^^^^^^^

Although it is almost never necessary to install Pootle as a Python package, it
is possible. This might be useful for packagers of Linux distributions, for
example.

To install Pootle just the run following command from within the Pootle
directory::

    cd Pootle-2.1.1
    ./setup.py install

To start Pootle simply run::

    PootleServer

You should be able to access the server at localhost on port 8080.

If you need to run Pootle under a different port execute::

    PootleServer --port=PORTNUMBER

The first time you visit a new Pootle install it will take some time to setup
its database and to recalculate statistics and search indexes for the default
translation projects.

By default *setup.py* will use the directory */var/lib/pootle* for
translation files, databases and other working files Pootle might use. The user
running will need to have write permissions on this directory and all its
descendant files and subdirectories.

To verify which version of Pootle and dependencies you have installed run::

    [l10n@server]# PootleServer --version
    Pootle 2.1.1
    Translate Toolkit 1.8.0
    Django 1.2.1


.. _installation#auto_start_pootle:

Auto start Pootle
^^^^^^^^^^^^^^^^^

Installation will prepare your system to start Pootle server automatically as a
daemon. The only thing left to do is to enable the daemon for auto start.
Therefor You have to modify */etc/default/pootle* file, which is read by
*/etc/init.d/pootle* script. Look for the line starting with
``POOTLE_ENABLE=`` and change value after equal sign to ``Yes``. Test results
by issuing the following command (don't forget to switch user account to
`pootle` before!): service pootle start

If you have difficulty installing please email the `translate-pootle
<https://lists.sourceforge.net/lists/listinfo/translate-pootle>`_ list with
details of exactly what you did and what didn’t work. If possible, please
include the output of ``PootleServer --version``.


.. _installation#manually_updating_statistics:

Manually updating statistics
----------------------------

.. versionchanged:: 2.1

Files are not kept in sync any more.  If you need to perform manual work on the
files, be sure to read the section on the :doc:`command line actions
<commands>` to ensure that you and Pootle work with the same information.


.. _installation#other_deployment_scenarios:

Other deployment scenarios
--------------------------

The easiest way to run Pootle is using ``PootleServer`` as described above,
however installations with a large number of users are better off :doc:`running
under apache <apache>`. You might also consider using :doc:`nginx` if you
prefer it.

By default Pootle is configured to use SQLite for its main database, but using
:ref:`installation#mysql` or PostgreSQL is strongly recommended rather than
SQLite for real installations.  You can :doc:`migrate your database
<database_migration>` to another database system if you already have valuable
data.


.. _installation#mysql:

MySQL
^^^^^

Using MySQL is well tested and recommended.  You can :doc:`migrate your current
database <database_migration>` if you already have data you don't want to lose.

To use a MySQL database for Pootle instead of the default SQLite you need to
create a new database and database user:

.. code-block:: mysql

   $ mysql -u root -p
   > CREATE DATABASE pootle CHARACTER SET = 'utf8';
   > GRANT ALL PRIVILEGES ON pootle.* TO pootle@localhost IDENTIFIED BY 'pootlepassword';
   > FLUSH PRIVILEGES;

Next edit the */etc/pootle/localsettings.py* file (found under the main Pootle
directory if running from checkout) and modify the ``DATABASE_*`` options to
use your newly created database::

    DATABASE_ENGINE = 'mysql'               # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
    DATABASE_NAME = 'pootle'                # Or path to database file if using sqlite3.
    DATABASE_USER = 'pootle'                # Not used with sqlite3.
    DATABASE_PASSWORD = 'pootlepassword'    # Not used with sqlite3.
    DATABASE_HOST = ''                      # Set to empty string for localhost. Not used with sqlite3.
    DATABASE_PORT = ''                      # Set to empty string for default. Not used with sqlite3.

Database tables and initial data will be created on the first visit to Pootle.


.. _installation#advanced_settings:

Advanced settings
-----------------

Read through all the settings in *localsettings.py*  (or
*/etc/pootle/localsettings.py*)  All the options are well documented.  If you
have upgraded, you might want to compare your previous copy to the one
distributed with the Pootle version for any new settings you might be
interested in.  Many of these settings can improve performance drastically.
Also consult the page about :doc:`Pootle optimization <optimization>`.
