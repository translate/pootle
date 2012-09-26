.. _machine_translation:

Machine Translation
===================

.. versionadded:: 2.1

Pootle has the ability to use online Machine Translation (MT) Services to give
suggestions to translators. This feature has to be enabled by the server
administrators.


.. _machine_translation#using_machine_translation:

Using Machine Translation
-------------------------

.. note::

    Machine Translations are not meant to replace human translations but to
    give a general idea or understanding of the source text. It can be used
    as suggestion of a translation, but don't forget to review the
    suggestion given.

If the server administrator has enabled machine translation then an icon will
be displayed for each source text (English or alternative source language) next
to the Copy button. Clicking the relevant buttons will retrieve translation
suggestions from the online services and will mark the current unit as fuzzy
to indicate that review is required.


.. _machine_translation#how_to_enable_machine_translations:

Enabling Machine Translations
-----------------------------

To enable a certain Machine Translation Service, edit
:file:`settings/60-translation.conf` and uncomment the line regarding the
desired service within the ``MT_BACKENDS`` setting.

Each line is a tuple which has the name of the service and an optional API key.
Some services may not require API keys but others do, so please take care of
getting an API key when necessary.


.. _machine_translation#machine_translation_services:

Available Machine Translation services
--------------------------------------

Supported Services:
- Google Translate
- Apertium.

Google Translate is widely used and supports many `translation pairs
<https://code.google.com/intl/eu/apis/ajaxlanguage/documentation/#supportedpairs>`_.
It is now a paid service requiring an account and API key.

On the other hand, Apertium is best suited for close language pairs. Especially
for those languages spoken in the Iberian Peninsula that are similar.
