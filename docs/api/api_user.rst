.. _api-user-resources:

User resources
**************

The Pootle API exposes a number of resources. Next you have a complete list of
User specific resources.

.. note:: All URLs listed here should be :ref:`appended to the base URL of the
   API <using-pootle-api#how-to-perform-queries>`.


.. _api-user-resources#create-user:

Create a user
=============

:URL: ``/users/``
:Description: Creates a new user.
:API versions: 1
:Method: POST
:Returns: HTTP 201 response with the relative URL for the newly created user
          on its ``Location`` header.


.. _api-user-resources#get-user:

Get a user
==========

:URL: ``/users/<USER>/``
:Description: Returns the user with the ``<USER>`` ID.
:API versions: 1
:Method: GET
:Returns: User with ``<USER>`` ID.

.. code-block:: json

    {
        "date_joined": "2013-03-15T19:04:39.401505",
        "email": "admin@doesnotexist.com",
        "first_name": "Administrator",
        "last_name": "",
        "resource_uri": "/api/v1/users/3/",
        "username": "admin"
    }


.. _api-user-resources#change-user:

Change a user
=============

:URL: ``/users/<USER>/``
:Description: Changes the user with the ``<USER>`` ID.
:API versions: 1
:Method: PATCH or PUT
:Returns: HTTP 204 NO CONTENT response.

.. note:: The method used can be:

   * **PATCH** if the user is going to be partially changed (just some of its
     fields)
   * **PUT** if the whole user is going to be changed


.. _api-user-resources#delete-user:

Delete a user
=============

:URL: ``/users/<USER>/``
:Description: Deletes the user with the ``<USER>`` ID.
:API versions: 1
:Method: DELETE
:Returns: HTTP 204 NO CONTENT response.
