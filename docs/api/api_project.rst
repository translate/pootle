.. _api-project-resources:

Project resources
*****************

The Pootle API exposes a number of resources. Next you have a complete list of
:ref:`Project <glossary#project>` specific resources.

.. note:: All URLs listed here should be :ref:`appended to the base URL of the
   API <using-pootle-api#how-to-perform-queries>`.


.. _api-project-resources#list-projects:

List projects
=============

:URL: ``/projects/``
:Description: Returns the projects list.
:API versions: 1
:Method: GET
:Returns: List of projects.

.. code-block:: json

    {
        "meta": {
            "limit": 1000,
            "next": null,
            "offset": 0,
            "previous": null,
            "total_count": 4
        },
        "objects": [
            {
                "backlink": "http://pootle.locamotion.org/projects/firefox/",
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
            },
            {
                "backlink": "http://pootle.locamotion.org/projects/lxde/",
                "checkstyle": "standard",
                "code": "lxde",
                "description": "",
                "fullname": "LXDE",
                "ignoredfiles": "",
                "localfiletype": "po",
                "resource_uri": "/api/v1/projects/5/",
                "source_language": "/api/v1/languages/2/",
                "translation_projects": [
                    "/api/v1/translation-projects/88/",
                    "/api/v1/translation-projects/89/",
                    "/api/v1/translation-projects/90/"
                ],
                "treestyle": "nongnu"
            }
        ]
    }


.. _api-project-resources#create-project:

Create a project
================

:URL: ``/projects/``
:Description: Creates a new project.
:API versions: 1
:Method: POST
:Returns: HTTP 201 response with the relative URL for the newly created project
          on its ``Location`` header.


.. _api-project-resources#get-project:

Get a project
=============

:URL: ``/projects/<PROJ>/``
:Description: Returns the project with the ``<PROJ>`` ID.
:API versions: 1
:Method: GET
:Returns: Project with ``<PROJ>`` ID.

.. code-block:: json

    {
        "backlink": "http://pootle.locamotion.org/projects/firefox/",
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


.. _api-project-resources#change-project:

Change a project
================

:URL: ``/projects/<PROJ>/``
:Description: Changes the project with the ``<PROJ>`` ID.
:API versions: 1
:Method: PATCH or PUT
:Returns: HTTP 204 NO CONTENT response.

.. note:: The method used can be:

   * **PATCH** if the project is going to be partially changed (just some of its
     fields)
   * **PUT** if the whole project is going to be changed


.. _api-project-resources#delete-project:

Delete a project
================

:URL: ``/projects/<PROJ>/``
:Description: Deletes the project with the ``<PROJ>`` ID.
:API versions: 1
:Method: DELETE
:Returns: HTTP 204 NO CONTENT response.


.. _api-project-resources#get-project-statistics:

Get statistics for a project
============================

:URL: ``/projects/<PROJ>/statistics/``
:Description: Returns the project with the ``<PROJ>`` ID, including an extra
              field with its statistics.
:API versions: 1
:Method: GET
:Returns: Project with ``<PROJ>`` ID and its statistics.

.. code-block:: json

    {
        "backlink": "http://pootle.locamotion.org/projects/firefox/",
        "checkstyle": "standard",
        "code": "firefox",
        "description": "",
        "fullname": "Firefox 22 (Aurora)",
        "ignoredfiles": "",
        "localfiletype": "po",
        "resource_uri": "/api/v1/projects/4/",
        "source_language": "/api/v1/languages/2/",
        "statistics": {
            "errors": 0,
            "fuzzy": {
                "percentage": 1,
                "units": 1,
                "words": 7
            },
            "suggestions": 5,
            "total": {
                "percentage": 100,
                "units": 289,
                "words": 1309
            },
            "translated": {
                "percentage": 99,
                "units": 284,
                "words": 1296
            },
            "untranslated": {
                "percentage": 0,
                "units": 4,
                "words": 6
            }
        },
        "translation_projects": [
            "/api/v1/translation-projects/71/",
            "/api/v1/translation-projects/72/",
            "/api/v1/translation-projects/73/",
            "/api/v1/translation-projects/74/"
        ],
        "treestyle": "nongnu"
    }
