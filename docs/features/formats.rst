.. _formats:

File formats
============

Pootle supports :ref:`many file formats <toolkit:formats>` through the powerful
*Translate Toolkit* API.  The Toolkit also provides several :ref:`format
converters <toolkit:commands#converters>` for other formats, this will allow
you to host a lot of translatable content on Pootle.

All these formats can be downloaded for offline use/or translation (for example
in Virtaal). We recommend *Virtaal* for offline translation. They can also be
downloaded in XLIFF format.


.. _formats#bilingual:

Bilingual formats
-----------------

These formats are translation files that include the source and target language
in one file.

- :ref:`Gettext PO <toolkit:po>`

- :ref:`XLIFF <toolkit:xliff>`


.. versionadded:: 2.0.3

- :ref:`Qt TS <toolkit:ts>`

- :ref:`TBX <toolkit:tbx>`

- :ref:`TMX <toolkit:tmx>`


.. _formats#monolingual:

Monolingual formats
-------------------

.. versionadded:: 2.1

These files contain only one language in the file. Pootle supports formats
without conversion.

- :ref:`Java properties <toolkit:properties>`
- :ref:`Mac OSX strings <toolkit:strings>`
- :ref:`PHP arrays <toolkit:php>`
- :ref:`Subtitles <toolkit:subtitles>` in many formats

Monolingual files need special attention in order to provide translators with
good workflow and to assist to perform good translation.  Read more in the
localization guide.

The main difference between monolingual and bilingual projects in Pootle is
that for monolingual projects a translation template is required. Pootle cannot
meaningfully import strings from monolingual files unless the original text is
present.

Either the source language or the :ref:`special Templates language
<templates#the_templates_language>` must be added to the project and their
files uploaded before other languages are added. Files found in either will be
considered template files (in the case where both templates and source language
exist templates will be used).

What users will see when translating monolingual file is a matching between
strings in the templates file and strings in the target language files. The
matching is format specific (for example in subtitles the matching is based on
timestamps, for Java properties it is based on keys, etc.)

While Pootle supports uploading translations in the monolingual format this
should be limited to importing old translations. Users who want to translate
offline should download the XLIFF version.

When tracking monolingual files with version control, if the file structure
changes (e.g. new strings are added) then source files must be updated first.

Apart from these considerations monolingual projects will feel and behave the
same as bilingual projects, all of Pootle's features are available to
administrators and translators.

You can still use the format converters from the Translate Toolkit to host
these monolingual file formats as a Gettext PO project.  This has the advantage
that files in version control always have the source and target strings
together and you are able to integrate with external PO tools.
