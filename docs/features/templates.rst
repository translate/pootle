
.. _templates:

Translation templates
=====================

Translation templates are translation files that contain only the source text
(original text). These files are used as a template to create target files for
each language.

Users familiar with Gettext know translation templates as POT files. For other
bilingual formats (like XLIFF) untranslated files with the same extension are
used as templates.


.. _templates#the_templates_language:

The *"Templates"* language
--------------------------

Pootle can manage a special language called *Templates*. This is not strictly
speaking a language but rather a place to store translation templates for a
project.

If the *Templates* language is present then Pootle will initialise brand new
languages from the *Templates* files present in Pootle.

If the *Templates* language is absent from a project, Pootle will assume all
initialisation of files for new languages happens outside of Pootle.


.. _templates#starting_a_new_translation:

Starting a new translation
--------------------------

It is helpful to understand in more detail how a new language is created or
added to Pootle.

When adding a new language to a project from the Pootle interface, and the
*Templates* language exists for the project in Pootle then a fresh copy
will be generated based on those template files.

If there is no *Templates* language it is necessary to manage all
initialisation of languages from the Pootle command line.  When using
:djadmin:`update_stores` new languages will be initialised if they are present
on the filesystem. You are responsible for initialisation of these new
languages from template files as required.


.. _templates#updating_translations:

Updating existing translations
------------------------------

Pootle will not update existing translations if new template files are added
to Pootle. Updating of translations is managed outside of Pootle.  You can
update your translations as follows:

#. Use :djadmin:`sync_stores` to sync all translations to the filesystem.
   These files will now contain the latest translations from Pootle users.
#. Use :ref:`pot2po <toolkit:pot2po>` or similar to update the translations.
#. Use :djadmin:`update_stores` to push the updated translations to Pootle.


A detailed example can be found in :ref:`Updating strings for existing project
<project_setup#updating-strings>`.
