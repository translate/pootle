Older releases
==============

Older release more for your entertainment and to track Pootle's history.


Version 2.1
-----------

Released on August 17th 2010.

- Pootle no longer depends on statsdb and SQLite.

- Files on disk are only synced with the database on download or commit.
  The old behaviour can be restored at the cost of performance.
  A ``manage.py`` :ref:`command <commands>` can sync to files on the
  command line.

- The database is now much larger. This should have no negative impact
  on performance, but we strongly suggest using MySQL or PostgreSQL
  for the best performance.

- Pootle 2.1 will upgrade the database automatically from Pootle 2.0
  installations. You need to have South installed. Install it from your
  distribution, or http://south.aeracode.org/ or with ``easy_install South``
  (the upgrade could take quite a while, depending on your installation size).

- Pending files are not used for suggestions any more, and will also be
  migrated to the database during upgrade.

- New settings are available in `localsettings.py` -- compare your
  existing one to the new one.

- Pootle 1 installations can easily migrate everything excluding project
  permissions. We encourage administrators to configure permissions with
  the new permission system which is much simpler to use, since permissions
  on the language and project level are now supported.

- Have a look at the optimization guide to ensure your Pootle runs well.


Version 2.0
-----------

Released on December 7th 2009.

- Pootle now uses the Django framework and data that previously was stored
  in flat files (projects, languages, users and permissions) is now stored
  in a database. Migration scripts are provided.

- Review all suggestions before migrating, and note that assignments
  are not yet supported in Pootle 2.0.


Version 1.2.0
-------------

Released on October 8th 2008.

- The name of the directory for indexing databases changed from
  `.poindex-PROJECT-LANGUAGE` to `.translation_index`. Administrators
  may want to remove the old indexing directories manually.

- The enhanced search function needs all indexing databases to be
  regenerated, otherwise it won't find anything. To achieve this, just
  remove all `.translation_index` directories under your projects::

    find /path/to/projects/ -type d -name ".translation_index" -exec rm -rf {} \;

- If you used testing versions of Pootle 1.2, you almost definitely need
  to regenerate your statistics database. Pootle might be able to do it
  automatically, but if not, delete `~/.translate_toolkit/stats.db`.


Version 1.0
-----------

Released on May 25th 2007.

XLIFF support
  Pootle 1.0 is the first version with support for XLIFF based projects.
  In the admin interface the project type can be specified as PO / XLIFF
  (this really just tells Pootle for which type of files it should look -
  it won't convert your project for you). This property is stored in
  `pootle.prefs` in the variable ``localfiletype`` for each project.

Configurable logos
  You are now able to configure the logos to use in `pootle.prefs`. At the
  moment it will probably be easiest to ensure that the same image sizes
  are used as the standard images.

Localized language names
  Users can now feel more at home with language names being localized.
  This functionality is actually provided by the toolkit and your system's
  iso-codes package.

Treestyle: gnu vs nongnu
  Pootle automatically detects the file layout of each project. If you want
  to eliminate the detection process (which can be a bit slow for big
  projects) or want to override the type that Pootle detected, you can
  specify the ``treestyle`` attribute for the project in `pootle.prefs`.
  Currently this can not be specified through the admin interface.


Version 0.11
------------

Released on March 8th 2007.

- If the user has the appropriate privileges (ovewrite right) he/she will
  be able to upload a file and completely overwrite the previous one.
  Obviously this should be done with care, but was a requested feature for
  people that want to entirely replace existing files on a Pootle server.

- The server administrator can now specify the default access rights
  (permissions) for the server. This is the rights that will be used for
  all projects where no other setup has been given. See pootle.prefs for
  some examples.

- The default rights in the default Pootle setup has changed to only
  allow suggesting and to not allow translation. This means that the default
  server setup is not configured to allow translation, and that users must
  be specifically assigned the translate (and optionally review) right, or
  alternatively, the default rights must be configured to allow translation
  (see the paragraph above).

- The baseurl will now be used, except for the `/doc/` directory, that
  currently still is offered at `/doc/`.

- The default installation now uses English language names in preperation
  for future versions that will hopefully have language names translated
  into the user interface language. To this end the language names must be
  in English, and names with country codes must have the country code in
  simple noun form in brackets. For example `Portuguese (Brazil)`; in other
  words, not `Portuguese (Brazilian)`.


Version 0.10
------------

Released on August 29th 2006.

Statistics
  The statistics pages are greatly reworked.  We now have a page that shows
  a nice table, that you can sort, with graphs of the completeness of the
  files.  This is the default view.  What is confusing is that the stats
  page does not work directly with editing.  To get the editing features,
  click on the editing link in the top bar.

  The quick statistics files (`pootle-projectname-zu.stats`) now also
  store the fuzzy stats that are needed to render the statistics tables.
  Your previous files from 0.9 can not supply this information. Pootle 0.10
  will automatically update these files, but if you (for some reason)
  want/need to go back to Pootle 0.9, you will have to delete these files.
  Not all `.stats` files need to be deleted, only the ones starting with
  `pootle-projectname`.

SVN and CVS committing
  You can now commit to SVN or CVS.  A default commit message is added, you
  cannot edit this message.  Your ability to commit depends on the rights
  you have on the checkout and since you cannot supply a password it needs
  to be a non-blocking method.  This feature is probably not useful for a
  very public server unless it is managing multiple translations of your
  own project and you have direct control over it and CVS/SVN accounts.
  It will work well in a standalone situation like a Translate@thon etc,
  where it is a public event but the server is controled by yourself for
  the event and then you can simply commit changes at the end.
  For more information, see version control information.

Terminology
  Pootle can now aid translators with terminology. Terminology can be
  specified to be global per language, and can be overriden per project
  for each language. A project called "terminology" (with any full name)
  can contain any files that will be used for terminology matching.
  Alternatively a file with the name `pootle-terminology.po` can be put
  in the directory of the project, in which case the global one (in the
  terminology project) will not be used. Matching is done in real time.
  Note that this does not work with GNU-style projects (where all the
  files are in one directory and have names according to the language code).

Translation Memory
  Pootle can now aid translators by means of a translation memory. The
  suggestions are not generated realtime -- it is done on the server by
  means of a commandline program (`updatetm`). Files with an appended `.tm`
  will be generated and read by Pootle to supply the suggestions. For more
  information see `updatetm`.
