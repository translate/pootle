.. _api_tp_resources:

Translation project resources
*****************************

The Pootle API exposes a number of resources. Next you have a complete list of
Translation project specific resources.

.. note:: All paths should be appended to the base URL of the API:
   ``<SERVER>/api/<API_VERSION>/``.

.. note:: "translation projects" means "languages" in a "project".


.. _api_tp_resources#list_tps_in_project:

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
        "id": 4,
        "ignoredfiles": "",
        "localfiletype": "po",
        "report_target": "",
        "resource_uri": "/api/v1/projects/4/",
        "translation_projects": [
            "/api/v1/translation-projects/71/",
            "/api/v1/translation-projects/72/",
            "/api/v1/translation-projects/73/",
            "/api/v1/translation-projects/74/",
            "/api/v1/translation-projects/75/",
            "/api/v1/translation-projects/76/",
            "/api/v1/translation-projects/77/",
            "/api/v1/translation-projects/78/",
            "/api/v1/translation-projects/79/",
            "/api/v1/translation-projects/80/"
        ],
        "treestyle": "nongnu"
    }

