.. _api-tp-resources:

Translation project resources
*****************************

The Pootle API exposes a number of resources. Next you have a complete list of
:ref:`Translation project <glossary#translation-project>` specific resources.

.. note:: All URLs listed here should be :ref:`appended to the base URL of the
   API <using-pootle-api#how-to-perform-queries>`.


.. _api-tp-resources#list-tps-in-project:

List translation projects in a project
======================================

:URL: ``/projects/<PROJ>/``
:Description: Returns the translation projects (languages) list on a given
              ``<PROJ>`` project.
:API versions: 1
:Method: GET
:Returns: List of translation projects (languages) on a given ``<PROJ>``
          project.

.. code-block:: json

    {
        "checkstyle": "standard",
        "code": "firefox",
        "description": "",
        "fullname": "Firefox 22 (Aurora)",
        "ignoredfiles": "",
        "localfiletype": "po",
        "resource_uri": "/api/v1/projects/4/",
        "source_language": "/api/v1/languages/2/",
        "translation_projects": [
            "/api/v1/translation-projects/71/",
            "/api/v1/translation-projects/72/",
            "/api/v1/translation-projects/73/",
            "/api/v1/translation-projects/74/"
        ],
        "treestyle": "nongnu"
    }


.. _api-tp-resources#list-tps-in-language:

List translation projects in a language
=======================================

:URL: ``/languages/<LANG>/``
:Description: Returns the translation projects (projects) list on a given
              ``<LANG>`` language.
:API versions: 1
:Method: GET
:Returns: List of translation projects (projects) on a given ``<LANG>``
          language.

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


.. _api-tp-resources#create-tp:

Create a translation project
============================

:URL: ``/translation-projects/``
:Description: Creates a new translation project.
:API versions: 1
:Method: POST
:Returns: HTTP 201 response with the relative URL for the newly created
          translation project on its ``Location`` header.


.. _api-tp-resources#get-tp:

Get a translation project
=========================

:URL: ``/translation-projects/<TRPR>/``
:Description: Returns the translation project with the ``<TRPR>`` ID.
:API versions: 1
:Method: GET
:Returns: Translation project with ``<TRPR>`` ID.

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


.. _api-tp-resources#change-tp:

Change a translation project
============================

:URL: ``/translation-projects/<TRPR>/``
:Description: Changes the translation project with the ``<TRPR>`` ID.
:API versions: 1
:Method: PATCH or PUT
:Returns: HTTP 204 NO CONTENT response.

.. note:: The method used can be:

   * **PATCH** if the translation project is going to be partially changed (just
     some of its fields)
   * **PUT** if the whole translation project is going to be changed


.. _api-tp-resources#delete-tp:

Delete a translation project
============================

:URL: ``/translation-projects/<TRPR>/``
:Description: Deletes the translation project with the ``<TRPR>`` ID.
:API versions: 1
:Method: DELETE
:Returns: HTTP 204 NO CONTENT response.


.. _api-tp-resources#get-tp-statistics:

Get statistics for a translation project
========================================

:URL: ``/translation-projects/<TRAP>/statistics/``
:Description: Returns the translation project with the ``<TRAP>`` ID, including
              an extra field with its statistics.
:API versions: 1
:Method: GET
:Returns: Translation project with ``<TRAP>`` ID and its statistics.

.. code-block:: json

    {
        "description": "",
        "language": "/api/v1/languages/110/",
        "pootle_path": "/fr/Firefox/",
        "project": "/api/v1/projects/3/",
        "real_path": "Firefox/fr",
        "resource_uri": "/api/v1/translation-projects/65/",
        "statistics": {
            "errors": 0,
            "fuzzy": {
                "percentage": 4,
                "units": 1,
                "words": 7
            },
            "suggestions": 3,
            "total": {
                "percentage": 100,
                "units": 39,
                "words": 167
            },
            "translated": {
                "percentage": 94,
                "units": 37,
                "words": 157
            },
            "untranslated": {
                "percentage": 2,
                "units": 1,
                "words": 3
            }
        },
        "stores": [
            "/api/v1/stores/77/",
            "/api/v1/stores/76/",
            "/api/v1/stores/75/"
        ]
    }
