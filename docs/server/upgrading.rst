.. _upgrading:

Upgrading
=========

Pootle can easily be upgraded to newer versions.  Here are some tips to make
the process easier.

Familiarize yourself with :doc:`important changes <../changelog>` in Pootle
over the versions.  If you are upgrading to Pootle 2.x from Pootle 1.x, have a
look at the :doc:`database_migration` page first, although some of the issues
on this page could still be relevant.

Check the :doc:`installation` instructions for the newer version, and ensure
that you have all the dependencies for the newer version.

Always make backups of all your translation files (your whole
:setting:`PODIRECTORY`) and your custom settings file. You can synchronize all
your translation files with the database using the :ref:`sync_stores
management command <commands#sync_stores>` before you make your backups.

Make a backup of your complete database using the appropriate *dump* command
for your database system.

If you are upgrading from a version of Pootle that uses *localsettings.py* then
you want to make sure your configuration file is read when Pootle starts. For
more information, read the :ref:`settings#customizing` section.

You might want to look for any new :ref:`available settings
<settings#available>` in the new version that you might want to configure.

Once you have the new code configured to run in your web server using the
correct settings file, you will be ready to run the database upgrade
procedure by using the :ref:`updatedb management command
<commands#updatedb>`.

After a successful upgrade, consider clearing your cache. For users of
memcached it is enough to restart memcached. For users of the default database
cache, you can drop the `pootlecache` table and recreate it with::

    $ pootle createcachetable pootlecache


.. _upgrading#custom_changes:

Custom Changes
--------------

If you made any changes to Pootle code, templates or styling, you will want to 
ensure that your upgraded Pootle contains those changes.  How hard that is will
depend entirely on the details of these changes.

Changes made to the base template are likely to work fine, but changes to
details will need individual inspection to see if they can apply
cleanly or have to be reimplemented on the new version of Pootle.

Since Pootle 2.5 :doc:`customization of style sheets and templates
<../developers/customization>` have become much easier to seperate from
the standard code.  If you are migrating to Pootle 2.5+ then use this
opportunity to move your code to the correct customization locations.
