.. _upgrading:

Upgrading
=========

Pootle can easily be upgraded to newer versions to get the benefit of the
newest versions.  Here are some tips to make the process easier:

Familiarize yourself with :doc:`important changes <../changelog>` in Pootle
over the versions.  If you are upgrading to Pootle 2.x from Pootle 1.x, have a
look at the :doc:`database_migration` page first, although some of the issues
on this page could still be relevant.

Check the :doc:`installation` instructions for the newer version, and ensure
that you have all the dependencies for the newer version. The package "south"
is a requirement upgrading the database, for example.

If you are still using SQLite as your Pootle 2 database, you should look into
doing a :doc:`database_migration` to MySQL or Postgres for better performance.
It is recommended to do this with Pootle 2.0.6 before migrating to Pootle 2.1
(the upgrade will be faster this way). Don't perform a Pootle version upgrade
at the same time as a database migration. Finish the database migration
completely before upgrading Pootle (or the other way round).

Always make backups of all your translation files (your whole *podirectory*),
and your settings (*localsettings.py*).  With Pootle 2.1 there is a way to
synchronize all translation files with the database from the :doc:`command line
<commands>`.

Make a backup of your complete database using the appropriate *dump* command
for your database system.

You probably want to use your old *localsettings.py* with the new Pootle
version, or make all the same changes to the file that came with the version
you are upgrading to.  When you start the new version of Pootle, you want to be
sure that your *podirectory* and database settings are correct.  If you reuse
your old *localsettings.py*, you might want to look for any new settings that
are available in the new version that you might want to configure. For example,
the setting ``CONTACT_EMAIL`` was introduced in Pootle 2.1 - that would be
missing from a settings file from Pootle 2.0.

Once you have the new code configured to run in your web server using the
correct *localsettings.py*, **Pootle should perform the necessary upgrade when
the first page is requested**.

.. note::

    For certain upgrades this might take long, and you might prefer to run it
    from the command line before taking the server live.  Do this with the
    *updatedb* :doc:`management command <commands>`.


.. _upgrading#other_changes:

Other changes you made to Pootle
--------------------------------

If you made any changes to Pootle code, templates or styling, it will depend
entirely on the details of these changes how you migrate them to the new Pootle
version.

A diff from the original Pootle package you modified would allow you to keep
track of your changes.  Changes to the base template is likely to work fine,
but changes to details will need individual inspection to see if they can apply
cleanly or have to be reimplemented on the new version of Pootle.
