.. _offline:

Offline translation
===================

Pootle's strength is making translation management easy, allowing large teams
to collaborate while ensuring quality and consistency through :doc:`features
<index>` like :doc:`quality checks <checks>` and :doc:`terminology`, opening
the door for casual contributions and crowd-sourcing through
:doc:`suggestions`.

However experienced translators might still prefer to use a dedicated desktop
translation application.

Offline translation using whatever tool the user prefers can be integrated
within Pootle's workflow easily through downloading and uploading translation
files.

We recommend `Virtaal <http://virtaal.org>`_ for offline
translation, as it supports the same formats that Pootle supports, has all of
Pootle's features and power and more.


.. _offline#downloading:

Downloading
-----------

From the Translate tab in the translation project page users can download files
for offline translations.

Files are available in the original format and in :ref:`toolkit:xliff` format.
Bilingual formats are suitable for offline translation, but
:ref:`formats#monolingual` should be treated as just an export. If you want to
translate files offline from a monolingual project, it is best to download the
file as XLIFF.

XLIFF export will include all of the information in Pootle's database (like
suggestions, fuzzy, translators comment) even if the original format doesn't
support representing this information.

In case you want to work with multiple files at once, you can download the
whole translation project or the contents of a subdirectory as a ZIP archive.


.. _offline#uploading:

Uploading
---------

From the translation project page you can upload translations to Pootle.
Translations from the uploaded file will be merged with existing translations
in the database, the merge process depends on the merging method the user
selects, and the :doc:`permissions` the user has.


.. _offline#merging_methods:

Merging methods
^^^^^^^^^^^^^^^

Merge
  Translations in the uploaded file are accepted for currently untranslated
  strings. In case of conflict between the current file and the uploaded file,
  the new translations are turned into suggestions. The file structure will not
  change, new strings will be ignored. This requires the "translate"
  permission.

Suggest
  No translation is accepted, all new translations are added as suggestions.
  This requires the *suggest* permission.

Overwrite
  The current file is replaced with the uploaded version. All the current
  translations on Pootle are lost. The structure of the file may change with
  new strings introduced and some existing strings deleted. This requires the
  "overwrite" permission.


.. _offline#advanced_uploading:

Advanced uploading
^^^^^^^^^^^^^^^^^^

Most of the time, you'll be uploading files you directly downloaded from Pootle
— either in the original format or as XLIFF export. Pootle will match the
uploaded file with an existing file based on filename.

In case a file got renamed or you want to merge translations from a different
file (for example a translation compendium created by
:ref:`toolkit:pocompendium`) use the *Upload to* field to specify which
existing file to merge with.

Users with admin permissions can introduce new files by just uploading them.
When uploading a new file, the merge method is irrelevant.

Users can mass upload files using a ZIP archive. Pootle expects a ZIP file
similar to the one it exports. The selected merge method will apply to the
content of the archive on a file by file basis.

If a ZIP archive is selected, the *Upload to* field can be used to specify
the subdirectory to merge with.


.. _offline#caveats:

Caveats
^^^^^^^

Users with admin permissions should be very careful when uploading ZIP
archives. Mistakes in naming or incorrect *Upload to* choice can lead to
introduction of many spurious files.

Users with overwrite permissions should be careful when uploading ZIP archives,
as all files will be overwritten including ones that they may not have
translated. When overwriting, it is better to do it one file at a time.

Files of a different format can be uploaded, and will be converted on the fly,
but the merging behaviour is format specific and not always predictable. This
also applies to XLIFF files generated outside of Pootle. It is preferable to
always use the original format or the XLIFF file exported by Pootle.

Monolingual files can be uploaded, but this is not recommended for normal use.
To merge translations, a corresponding template file is required. The uploaded
file and the template file should have exactly the same structure. If their
versions differ, incorrect translations may be introduced. This is why we
recommend never using monolingual files for offline translations. Uploading
monolingual files should be used only when initially importing existing work.
