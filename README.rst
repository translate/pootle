
Pootle: a web translation and translation management engine
===========================================================

* How it works
* Running
* Manual preparation
* Notes
* Assignments
* Common problems
* Bug reporting/Feature requests
* References


How it works
------------

Pootle can host a number of translation projects for a number of languages.  It
allows a team to manage their files, permissions, projects, and also allows for
translation on-line.  Files can be downloaded for offline translation and later
uploaded again.

Pootle tries to lower the barrier of entry,  but also provides tools  to enable
teams to work towards higher quality while welcoming newcomers.


Running
-------

To run Pootle from sources, just run::

        ./PootleServer

After installation with setup.py, PootleServer should also be accessible from
the installation.

If you are more familiar with Django projects, you can look into the manage.py
commands as well.

Use ``--help`` to see the other options. The defaults will generally work.

Now visit http://localhost:8000/ to try out Pootle.

To stop the server, press Ctrl-C.

It is not recommended to run Pootle as the root user.  For any non-trivial
installation of Pootle, ensure that you use a database server (not SQLite) and
use memcached.  Other important information about optimisation is available in
the Pootle documentation:
<http://translate.sourceforge.net/wiki/pootle/optimisation>

Pootle can run under Apache using mod_python or mod_wsgi. Check this page for
detailed instructions:
<http://translate.sourceforge.net/wiki/pootle/apache>


Manual preparation
------------------

1. ``./manage.py syncdb``

   At this step, you will be asked to create a superuser.
   This user will be the administrator for your Pootle
   installation.

2. ``./manage.py initdb``

   This step fills the database with initial data needed
   to run Pootle.

3. ``./manage.py refresh_stats``

   Precalculate statistics and indexes for existing translation projects.
   This step is not strictly required, but without it Pootle will feel a bit
   sluggish and slow when visiting accessing a page for the first time.

4. ``./manage.py runserver``

   You can now visit your Pootle installation at 
   http://localhost:8000. Note that the first time will
   take a few moments to load, since Pootle needs to pre-compute
   stats data for the translation files.


Notes
-----

Files should be reindexed automatically. To ensure that all statistics and
indices are up to date for the current projects and languages, run::

        PootleServer --refreshstats


Assignments
-----------

Goals and assignments don't work at the moment, but should be re-instated soon.


Common problems
---------------

If you get an error such as
``sqlite3.OperationalError: unable to open database file``
then DATABASE_NAME in pootle/settings.py is pointing at an invalid directory.
The default directory name is 'dbs' - ensure that this exists, and is writable
for the user running Pootle.


Bug Reporting/Feature requests
------------------------------

You can always report bugs or feature requests on the mailing list but because
of the increase in users and the fact that bug reports do go missing it is
probably best to place your bug report in Bugzilla: http://bugs.locamotion.org/

If you have a traceback or a patch then please include it. Also please be quite
specific about how the bug occurred and what you expected to happen.

If this is a feature request then try to be specific about how you think this
feature should work.


References
----------

* Web: <http://translate.sourceforge.net/wiki/pootle/index>
* Bugzilla: <http://bugs.locamotion.org/>
* Mailing List: <https://lists.sourceforge.net/lists/listinfo/translate-pootle>
* IRC: #pootle on irc.freenode.org
