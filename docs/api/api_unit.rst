.. _api-unit-resources:

Unit resources
**************

The Pootle API exposes a number of resources. Next you have a complete list of
:ref:`Unit <glossary#unit>` specific resources.

.. note:: All URLs listed here should be :ref:`appended to the base URL of the
   API <using-pootle-api#how-to-perform-queries>`.


.. _api-unit-resources#list-units-in-store:

List units in a store
=====================

:URL: ``/stores/<STOR>/``
:Description: Returns the unit list on a given ``<STOR>`` store.
:API versions: 1
:Method: GET
:Returns: Unit list on a given ``<STOR>`` store.

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


.. _api-unit-resources#get-a-unit:

Get a unit
==========

:URL: ``/units/<UNIT>/``
:Description: Returns the unit with the ``<UNIT>`` ID.
:API versions: 1
:Method: GET
:Returns: Unit with ``<UNIT>`` ID.

.. code-block:: json

    {
        "commented_by": null,
        "commented_on": "2013-03-15T20:10:35.017844",
        "context": "This is a phrase, not a verb.",
        "developer_comment": "Translators: name of the option in the menu.",
        "locations": "fr/firefox/chrome/global/languageNames.properties.po:62",
        "mtime": "2013-05-12T17:51:49.786611",
        "resource_uri": "/api/v1/units/70316/",
        "source_f": "New Tab",
        "source_length": 29,
        "source_wordcount": 3,
        "state": 0,
        "store": "/api/v1/stores/76/",
        "submitted_by": "/api/v1/users/3/",
        "submitted_on": "2013-05-21T17:51:16.155000",
        "suggestions": [
            "/api/v1/suggestions/1/"
        ],
        "target_f": "",
        "target_length": 0,
        "target_wordcount": 0,
        "translator_comment": ""
    }


.. _api-unit-resources#change-a-unit:

Change a unit
=============

:URL: ``/units/<UNIT>/``
:Description: Changes the unit with the ``<UNIT>`` ID.
:API versions: 1
:Method: PATCH or PUT
:Returns: HTTP 204 NO CONTENT response.

.. note:: The method used can be:

   * **PATCH** if the unit is going to be partially changed (just
     some of its fields), for example when providing a translation
   * **PUT** if the whole unit is going to be changed
