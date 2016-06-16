.. _machine_translation:

Machine Translation
===================

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

If the server administrator has enabled machine translation then an icon
|icon:icon-web-translate| will be displayed for each source text (English or
alternative source language) next to the Copy button. Clicking the relevant
buttons will retrieve translation suggestions from the online services and
will mark the current string as fuzzy to indicate that review is required.


.. _machine_translation#how_to_enable_machine_translations:

Enabling Machine Translations
-----------------------------

To enable a certain Machine Translation Service, edit :ref:`your configuration
file <settings#customizing>` and add the desired service within the
:setting:`POOTLE_MT_BACKENDS` setting.

Each line is a tuple which has the name of the service and an optional API key.
Some services may not require API keys but others do, so please take care of
getting an API key when necessary.


.. _machine_translation#machine_translation_services:

Available Machine Translation Services
--------------------------------------

Supported Services:

|icon:icon-google-translate| Google Translate

|icon:icon-yandex-translate| Yandex.Translate

.. versionadded:: 2.7 Yandex.Translate

Google Translate is widely used and supports a number of `languages`_.
It is a `paid service`_ requiring an account and API key.

.. _languages:  https://cloud.google.com/translate/v2/translate-reference#supported_languages
.. _paid service: https://cloud.google.com/translate/v2/pricing

`Yandex.Translate`_ is the free alternative to Google.

.. _Yandex.Translate: https://tech.yandex.com/translate/
