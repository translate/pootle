.. _api-suggestion-resources:

Suggestion resources
********************

The Pootle API exposes a number of resources. Next you have a complete list of
Suggestion specific resources.

.. note:: All URLs listed here should be :ref:`appended to the base URL of the
   API <using-pootle-api#how-to-perform-queries>`.


.. _api-suggestion-resources#list-suggestions-for-a-unit:

List suggestions for a unit
===========================

:Description: Returns the suggestion list for a given ``<UNIT>`` unit.
:API versions: 1
:Method: GET
:Returns: Suggestion list on a given ``<UNIT>`` unit.

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
            "/api/v1/suggestions/1/",
            "/api/v1/suggestions/3/"
        ],
        "target_f": "",
        "target_length": 0,
        "target_wordcount": 0,
        "translator_comment": ""
    }


.. _api-suggestion-resources#create-suggestion:

Create a suggestion
===================

:URL: ``/suggestions/``
:Description: Creates a new suggestion.
:API versions: 1
:Method: POST
:Returns: HTTP 201 response with the relative URL for the newly created
          suggestion on its ``Location`` header.


.. _api-suggestion-resources#get-suggestion:

Get a suggestion
================

:URL: ``/suggestions/<SUGG>/``
:Description: Returns the suggestion with the ``<SUGG>`` ID.
:API versions: 1
:Method: GET
:Returns: Suggestion with ``<SUGG>`` ID.

.. code-block:: json

    {
        "resource_uri": "/api/v1/suggestions/1/",
        "target_f": "Nouvel onglet",
        "translator_comment_f": "",
        "unit": "/api/v1/units/70316/"
    }


.. _api-suggestion-resources#change-suggestion:

Change a suggestion
===================

:URL: ``/suggestions/<SUGG>/``
:Description: Changes the suggestion with the ``<SUGG>`` ID.
:API versions: 1
:Method: PATCH or PUT
:Returns: HTTP 204 NO CONTENT response.

.. note:: The method used can be:

   * **PATCH** if the suggestion is going to be partially changed (just some of
     its fields)
   * **PUT** if the whole suggestion is going to be changed


.. _api-suggestion-resources#delete-suggestion:

Delete a suggestion
===================

:URL: ``/suggestion/<SUGG>/``
:Description: Deletes the suggestion with the ``<SUGG>`` ID.
:API versions: 1
:Method: DELETE
:Returns: HTTP 204 NO CONTENT response.
