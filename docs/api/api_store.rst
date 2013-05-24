.. _api-store-resources:

Store resources
***************

The Pootle API exposes a number of resources. Next you have a complete list of
:ref:`Store <glossary#store>` specific resources.

.. note:: All URLs listed here should be :ref:`appended to the base URL of the
   API <using-pootle-api#how-to-perform-queries>`.


.. _api-store-resources#list-stores-in-tp:

List stores in a translation project
====================================

:URL: ``/translation-projects/<TRPR>/``
:Description: Returns the store (file) list on a given ``<TRPR>`` translation
              project.
:API versions: 1
:Method: GET
:Returns: Store (file) list on a given ``<TRPR>`` translation project.

.. code-block:: json

    {
        "description": "",
        "language": "/api/v1/languages/110/",
        "pootle_path": "/fr/Firefox/",
        "project": "/api/v1/projects/3/",
        "real_path": "Firefox/fr",
        "resource_uri": "/api/v1/translation-projects/65/",
        "stores": [
            "/api/v1/stores/77/",
            "/api/v1/stores/76/",
            "/api/v1/stores/75/"
        ]
    }


.. _api-store-resources#get-store:

Get a store
===========

:URL: ``/stores/<STOR>/``
:Description: Returns the store with the ``<STOR>`` ID.
:API versions: 1
:Method: GET
:Returns: Store with ``<STOR>`` ID.

.. code-block:: json

    {
        "file": "/media/Firefox/fr/chrome/global/languageNames.properties.po",
        "name": "languageNames.properties.po",
        "pending": null,
        "pootle_path": "fr/firefox/chrome/global/languageNames.properties.po",
        "resource_uri": "/api/v1/stores/76/",
        "state": 2,
        "sync_time": "2013-03-15T20:10:35.070238",
        "tm": null,
        "translation_project": "/api/v1/translation-projects/65/",
        "units": [
            "/api/v1/units/70316/",
            "/api/v1/units/70317/",
            "/api/v1/units/70318/",
            "/api/v1/units/70319/"
        ]
    }


.. _api-store-resources#get-store-statistics:

Get statistics for a store
==========================

:URL: ``/stores/<STOR>/statistics/``
:Description: Returns the store with the ``<STOR>`` ID, including an extra field
              with its statistics.
:API versions: 1
:Method: GET
:Returns: Store with ``<STOR>`` ID and its statistics.

.. code-block:: json

    {
        "file": "/media/Firefox/fr/chrome/global/languageNames.properties.po",
        "name": "languageNames.properties.po",
        "pending": null,
        "pootle_path": "fr/firefox/chrome/global/languageNames.properties.po",
        "resource_uri": "/api/v1/stores/76/",
        "state": 2,
        "statistics": {
            "errors": 0,
            "fuzzy": {
                "percentage": 26,
                "units": 1,
                "words": 7
            },
            "suggestions": 1,
            "total": {
                "percentage": 100,
                "units": 4,
                "words": 27
            },
            "translated": {
                "percentage": 63,
                "units": 2,
                "words": 17
            },
            "untranslated": {
                "percentage": 11,
                "units": 1,
                "words": 3
            }
        },
        "sync_time": "2013-03-15T20:10:35.070238",
        "tm": null,
        "translation_project": "/api/v1/translation-projects/65/",
        "units": [
            "/api/v1/units/70316/",
            "/api/v1/units/70317/",
            "/api/v1/units/70318/",
            "/api/v1/units/70319/"
        ]
    }
