
.. _templates:

Translation templates
=====================

Translation templates are translation files that contain only the source text
(original text). These files are used as a template to create target files for
each language.

Users familiar with Gettext know translation templates as POT files. For other
bilingual formats (like XLIFF) untranslated files with the same extension will
be used as templates. For :ref:`formats#monolingual` the files representing the
source language are used as templates.


.. _templates#the_templates_language:

The *"Templates"* language
--------------------------

Pootle has a special language called templates. This is not strictly speaking a
language but rather a place to store translation templates for a project.

If the templates language is absent from a project, Pootle will assume files
under the project's source language are translation templates.

Gettext PO projects should always use a templates project where POT files can
be uploaded.  For simple projects (and most monolingual formats) it will be
simpler to use the source language.


.. _templates#starting_a_new_translation:

Starting a new translation
--------------------------

When adding a new language to a project, Pootle will first scan the file system
and look for translation files for that language. If none are present a fresh
copy will be generated based on the templates files (in a manner similar to
:ref:`pot2po <toolkit:pot2po>`).


.. _templates#updating_against_templates:

Updating against templates
--------------------------

When the document or software being translated is updated, Pootle helps you
retain old translation through the translation templates feature.

The templates files should be replaced with new versions (i.e. upload the new
versions to the templates language). Users with admin permission in the project
can use the *Update against templates* checkbox in the project admin page to
update languages to the newer version.

Users with admin permissions over a language can update this single language
from the files tab for the translation project.

This will update both the files and the database retaining old translations and
using fuzzy matching to match translations when the source text had minor
changes (in a manner similar to pot2po). Fuzzy matched strings will be marked
as fuzzy.
