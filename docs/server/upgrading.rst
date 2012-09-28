.. _upgrading:

Upgrading
=========

Pootle can easily be upgraded to newer versions.  Here are some tips to make
the process easier:

Familiarize yourself with :doc:`important changes <../changelog>` in Pootle
over the versions.  If you are upgrading to Pootle 2.x from Pootle 1.x, have a
look at the :doc:`database_migration` page first, although some of the issues
on this page could still be relevant.

Check the :doc:`installation` instructions for the newer version, and ensure
that you have all the dependencies for the newer version. For example, the
``south`` package is a requirement upgrading the database.

If you are still using SQLite as your Pootle 2 database, you should consider
performing a :doc:`database_migration` to MySQL or Postgres for better
performance.  It is recommended to do this with Pootle 2.0.6 before migrating
to Pootle 2.* (the upgrade will be faster this way). Don't perform a Pootle
version upgrade at the same time as a database migration. Finish the database
migration completely before upgrading Pootle (or the other way round).

Always make backups of all your translation files (your whole *podirectory*),
and your settings (*localsettings.py* or *settings/90-local.conf*).  With
Pootle 2.1+ you can synchronize all translation files with the database
using the ``syncdb`` :doc:`command <commands>` before you make your backups.

Make a backup of your complete database using the appropriate *dump* command
for your database system.

If you are upgrading from a version of Pootle that uses *localsettings.py* then
you want to move all your customized settings from *localsettings.py* into
the *settings/90-local.conf* file in your new Poole version.

You might want to look for any new settings that are available in the new
version that you might want to configure. For example, the setting
:setting:`CONTACT_EMAIL` was introduced in Pootle 2.1 - that would be
missing from a settings file from Pootle 2.0.

When you start the new version of Pootle, you want to be sure that your
*podirectory* and database settings are correct.

Once you have the new code configured to run in your web server using the
correct *settings/\*.conf*, **Pootle will perform the necessary upgrade when
the first page is requested**.

.. note::

    For certain upgrades this automated upgrade might take a long time. In such
    cases you might prefer to perform the upgrade from the command line before
    taking the server live.  Do this with the *updatedb* :doc:`management
    command <commands>`.


.. _upgrading#other_changes:

Other changes you made to Pootle
--------------------------------

If you made any changes to Pootle code, templates or styling, you will want to 
ensure that you upgraded Pootle contains those changes.  How hard that is will
depend entirely on the details of these changes.

A diff of your changes against the original Pootle package you modified will
allow you to keep track of your changes and apply them to the new Pootle.

Changes made to the base template are likely to work fine, but changes to
details will need individual inspection to see if they can apply
cleanly or have to be reimplemented on the new version of Pootle.

Since Pootle 2.2 customisation of style sheets and templates have become much
easier to seperate from the standard code.  If you are migrating to Pootle 2.2+
then use this opportunity to move your code to the correct customisation
locations.
