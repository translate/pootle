.. _api-language-resources:

Language resources
******************

The Pootle API exposes a number of resources. Next you have a complete list of
:ref:`Language <glossary#language>` specific resources.

.. note:: All URLs listed here should be :ref:`appended to the base URL of the
   API <using-pootle-api#how-to-perform-queries>`.


.. _api-language-resources#list-languages:

List languages
==============

:URL: ``/languages/``
:Description: Returns the languages list.
:API versions: 1
:Method: GET
:Returns: List of languages.

.. code-block:: json

    {
        "meta": {
            "limit": 1000,
            "next": null,
            "offset": 0,
            "previous": null,
            "total_count": 132
        },
        "objects": [
            {
                "code": "af",
                "description": "",
                "fullname": "Afrikaans",
                "nplurals": 2,
                "pluralequation": "(n != 1)",
                "resource_uri": "/api/v1/languages/3/",
                "specialchars": "ëïêôûáéíóúý",
                "translation_projects": [
                    "/api/v1/translation-projects/2/",
                    "/api/v1/translation-projects/3/"
                ]
            },
            {
                "code": "ak",
                "description": "",
                "fullname": "Akan",
                "nplurals": 2,
                "pluralequation": "(n > 1)",
                "resource_uri": "/api/v1/languages/4/",
                "specialchars": "ɛɔƐƆ",
                "translation_projects": [
                    "/api/v1/translation-projects/4/"
                ]
            }
        ]
    }


.. _api-language-resources#list-languages-matching-a-criteria:

List languages matching a criteria
==================================

:URL: ``/languages/?<CRITERIA>``
:Description: Returns a languages list that match the ``<CRITERIA>``.
:API versions: 1
:Method: GET
:Returns: Language list that match a given ``<CRITERIA>``.

``<CRITERIA>`` is a :wp:`query string <Query_string>` where the fields are
`Django ORM Field Lookups
<https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups>`_.
The available filtered fields and their filters are:

+---------------------------+-----------------------------------+
| Fields                    | Available filters (field lookups) |
+===========================+===================================+
| * ``code``                | * exact                           |
|                           | * iexact                          |
|                           | * contains                        |
|                           | * icontains                       |
|                           | * startswith                      |
|                           | * istartswith                     |
|                           | * endswith                        |
|                           | * iendswith                       |
+---------------------------+-----------------------------------+

A query to::

  http://pootle.locamotion.org/api/v1/languages/?code__exact=ak

will return:

.. code-block:: json

  {
      "meta": {
          "limit": 1000,
          "next": null,
          "offset": 0,
          "previous": null,
          "total_count": 1
      },
      "objects": [
          {
              "code": "ak",
              "description": "",
              "fullname": "Akan",
              "nplurals": 2,
              "pluralequation": "(n > 1)",
              "resource_uri": "/api/v1/languages/4/",
              "specialchars": "ɛɔƐƆ",
              "translation_projects": [
                  "/api/v1/translation-projects/4/"
              ]
          }
      ]
  }


.. _api-language-resources#create-language:

Create a language
=================

:URL: ``/languages/``
:Description: Creates a new language.
:API versions: 1
:Method: POST
:Returns: HTTP 201 response with the relative URL for the newly created language
          on its ``Location`` header.


.. _api-language-resources#get-language:

Get a language
==============

:URL: ``/languages/<LANG>/``
:Description: Returns the language with the ``<LANG>`` ID.
:API versions: 1
:Method: GET
:Returns: Language with ``<LANG>`` ID.

.. code-block:: json

    {
        "code": "gl",
        "description": "",
        "fullname": "Galician",
        "nplurals": 2,
        "pluralequation": "(n != 1)",
        "resource_uri": "/api/v1/languages/20/",
        "specialchars": "",
        "translation_projects": [
            "/api/v1/translation-projects/12/",
            "/api/v1/translation-projects/81/"
        ]
    }


.. _api-language-resources#change-language:

Change a language
=================

:URL: ``/languages/<LANG>/``
:Description: Changes the language with the ``<LANG>`` ID.
:API versions: 1
:Method: PATCH or PUT
:Returns: HTTP 204 NO CONTENT response.

.. note:: The method used can be:

   * **PATCH** if the language is going to be partially changed (just some of its
     fields)
   * **PUT** if the whole language is going to be changed


.. _api-language-resources#delete-language:

Delete a language
=================

:URL: ``/languages/<LANG>/``
:Description: Deletes the language with the ``<LANG>`` ID.
:API versions: 1
:Method: DELETE
:Returns: HTTP 204 NO CONTENT response.


.. _api-language-resources#get-language-statistics:

Get statistics for a language
=============================

:URL: ``/languages/<LANG>/statistics/``
:Description: Returns the language with the ``<LANG>`` ID, including an extra
              field with its statistics.
:API versions: 1
:Method: GET
:Returns: Language with ``<LANG>`` ID and its statistics.

.. code-block:: json

    {
        "code": "gl",
        "description": "",
        "fullname": "Galician",
        "nplurals": 2,
        "pluralequation": "(n != 1)",
        "resource_uri": "/api/v1/languages/20/",
        "specialchars": "",
        "statistics": {
            "errors": 0,
            "fuzzy": {
                "percentage": 1,
                "units": 1,
                "words": 1
            },
            "suggestions": 0,
            "total": {
                "percentage": 100,
                "units": 1191,
                "words": 1949
            },
            "translated": {
                "percentage": 91,
                "units": 1156,
                "words": 1767
            },
            "untranslated": {
                "percentage": 8,
                "units": 34,
                "words": 181
            }
        },
        "translation_projects": [
            "/api/v1/translation-projects/12/",
            "/api/v1/translation-projects/81/"
        ]
    }
