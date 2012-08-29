.. _machine_translation:

Machine Translation
===================

.. versionadded:: 2.1

Pootle has the ability to use online Machine Translation (MT) Services to give
suggestions to translators. This feature has to be enabled by the server
administrators.

.. _machine_translation#how_to_enable_machine_translations:

How to enable Machine Translations
----------------------------------

To enable a certain Machine Translation Service, edit *localsettings.py* and
uncomment the line regarding the desired service within the ``MT_BACKENDS``
setting.

Each line is a tuple which has the name of the service and an optional API key.
Some services may not require API keys but others do, so take care of getting
an API key when necessary.


.. _machine_translation#machine_translation_services:

Machine Translation services
----------------------------

.. note::

    Machine Translations are not meant to replace human translations but to
    give a general idea and understanding of the source text. Don't forget to
    review the suggestions given.

For now, a couple of online Machine Translation Services are available: Google
Translate and Apertium.

Google Translate is widely used and supports lots of `translation pairs
<https://code.google.com/intl/eu/apis/ajaxlanguage/documentation/#supportedpairs>`_.

On the other hand, Apertium is best suited for close language pairs, specially
for those languages spoken in the Iberian Peninsula that are similar.

If the server administrator has enabled either of those services, an icon will
be displayed for each source text (English or alternative source language) next
to the Copy button. Clicking the relevant buttons will retrieve translation
suggestions from the online services and will mark the current unit as fuzzy
for later review.
