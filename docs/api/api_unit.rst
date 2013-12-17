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


.. _api-unit-resources#list-units-matching-a-criteria:

List units matching a criteria
==============================

:URL: ``/units/?<CRITERIA>``
:Description: Returns a unit list that match the ``<CRITERIA>``.
:API versions: 1
:Method: GET
:Returns: Unit list that match a given ``<CRITERIA>``.

``<CRITERIA>`` is a :wp:`query string <Query_string>` where the fields are
`Django ORM Field Lookups
<https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups>`_.
Some examples might help:

* ``source_f`` field contains, case insensitive, *button*:
  ``/units/?source_f__icontains=button``
* ``target_f`` field starts with *window*:
  ``/units/?target_f__startswith=window``
* ``mtime`` field (modification datetime) is on the *May* month:
  ``/units/?mtime__month=05``
* Unit is translated: ``/units/?state=200``

Multiple field lookups can be provided, even several lookups on the same field:

``/units/?mtime__month=05&mtime__day=12&developer_comment__icontains=verb``

.. note:: It is not possible to provide **OR** conditions using filters, nor
   negate the filters.

+---------------------------+-----------------------------------+
| Fields                    | Available filters (field lookups) |
+===========================+===================================+
| * ``context``             | * exact                           |
| * ``developer_comment``   | * iexact                          |
| * ``locations``           | * contains                        |
| * ``source_f``            | * icontains                       |
| * ``target_f``            | * startswith                      |
| * ``translator_comment``  | * istartswith                     |
|                           | * endswith                        |
|                           | * iendswith                       |
+---------------------------+-----------------------------------+
| * ``commented_on``        | * year                            |
| * ``mtime``               | * month                           |
| * ``submitted_on``        | * day                             |
+---------------------------+-----------------------------------+
| * ``state``               | * exact                           |
| * ``store``               |                                   |
+---------------------------+-----------------------------------+

The available states are:

* **0** (untranslated): The unit is untranslated (empty)
* **50** (fuzzy): The unit is fuzzy (typically means translation needs more
  work)
* **200** (translated): The unit is fully translated
* **-100** (obsolete): The unit is no longer part of the store

.. warning:: It is possible to get all the units in a given store by requesting
   ``/units/?store=<STOR>`` but it is recommended to use the :ref:`List units
   in a store <api-unit-resources#list-units-in-store>` method instead.

   Filtering by store is only advisable when:

   * You need to provide extra filters:

     ``/units/?store=74&developer_comment__icontains=verb``

   * You want to get all the data for those units with a single request,
     despite the computational cost.


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
