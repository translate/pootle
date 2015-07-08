
.. _templates:

Translation templates
=====================

.. warning:: The whole concept around *templates* has been redefined in
  version 2.7, and what's described in this page doesn't work as expected
  for the time being.  The related work is tracked in :issue:`3877`.

Translation templates are translation files that contain only the source text
(original text). These files are used as a template to create target files for
each language.

Users familiar with Gettext know translation templates as POT files. For other
bilingual formats (like XLIFF) untranslated files with the same extension will
be used as templates.


.. _templates#the_templates_language:

The *"Templates"* language
--------------------------

Pootle has a special language called templates. This is not strictly speaking a
language but rather a place to store translation templates for a project.

If the templates language is absent from a project, Pootle will assume files
under the project's source language are translation templates.

Gettext PO projects should always use a templates project where POT files can
be uploaded.  For simple projects it will be simpler to use the source
language.


.. _templates#starting_a_new_translation:

Starting a new translation
--------------------------

When adding a new language to a project, Pootle will first scan the file system
and look for translation files for that language. If none are present a fresh
copy will be generated based on the templates files (in a manner similar to
:ref:`pot2po <toolkit:pot2po>`).
