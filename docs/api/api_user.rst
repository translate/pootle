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

.. note:: The consumer must have the appropiate permissions in order to be able
   to create new users.

.. warning:: The new user will have no password set, and therefore won't be
   able to log in until a password is set, either by an administrator or by the
   user requesting and setting a new password.


.. _api-user-resources#get-user:

Get a user
==========

:URL: ``/users/<USER>/``
:Description: Returns the user with the ``<USER>`` ID.
:API versions: 1
:Method: GET
:Returns: User with ``<USER>`` ID.

.. note:: The consumer will get the user data only if it is authenticated as
   the user which is trying to get the data for, or if it is a superuser.

   If the consumer is a superuser, then it will get all the resource data for
   its own resource, but for the other users resources will get only a
   restricted set of the fields.

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

.. note:: The consumer will only be able to change the data for a given user if
   it:

   * Is authenticated as the user which is trying to change the data for, and
   * Has enough permissions to perform this action.


.. _api-user-resources#delete-user:

Delete a user
=============

:URL: ``/users/<USER>/``
:Description: Deletes the user with the ``<USER>`` ID.
:API versions: 1
:Method: DELETE
:Returns: HTTP 204 NO CONTENT response.

.. note:: The consumer will only be able to delete a given user if it:

   * Is authenticated as the user which is trying to delete, and
   * Has enough permissions to perform this action.


.. _api-user-resources#get-user-statistics:

Get statistics for a user
=========================

:URL: ``/users/<USER>/statistics/``
:Description: Returns the user with the ``<USER>`` ID, including an extra field
              with its statistics.
:API versions: 1
:Method: GET
:Returns: User with ``<USER>`` ID and its statistics.

.. note:: If the consumer is authenticated as the same user for which the
   statistics are shown, then some extra fields are included in the response.

   This fields are the same ones that can be accessed when the consumer
   :ref:`gets the data for a user <api-user-resources#get-user>`.

.. code-block:: json

    {
        "resource_uri": "/api/v1/users/3/",
        "statistics": [
            [
                "Portuguese (Brazil) - pt_BR",
                [
                    ["/pt_BR/Firefox/",
                        [
                            {
                                "count": 2,
                                "id": "suggestions-pending",
                                "url": "/pt_BR/Firefox/translate.html#filter=user-suggestions&user=admin"
                            },
                            {
                                "count": 0,
                                "id": "suggestions-accepted",
                                "url": "/pt_BR/Firefox/translate.html#filter=user-suggestions-accepted&user=admin"
                            },
                            {
                                "count": 0,
                                "id": "suggestions-rejected",
                                "url": "/pt_BR/Firefox/translate.html#filter=user-suggestions-rejected&user=admin"
                            },
                            {
                                "count": 10,
                                "id": "submissions-total",
                                "url": "/pt_BR/Firefox/translate.html#filter=user-submissions&user=admin"
                            },
                            {
                                "count": 0,
                                "id": "submissions-overwritten",
                                "url": "/pt_BR/Firefox/translate.html#filter=user-submissions-overwritten&user=admin"
                            }
                        ]
                    ]
                ]
            ],
            [
                "Russian - ru",
                [
                    ["/ru/LXDE/",
                        [
                            {
                                "count": 0,
                                "id": "suggestions-pending",
                                "url": "/ru/LXDE/translate.html#filter=user-suggestions&user=admin"
                            },
                            {
                                "count": 0,
                                "id": "suggestions-accepted",
                                "url": "/ru/LXDE/translate.html#filter=user-suggestions-accepted&user=admin"
                            },
                            {
                                "count": 0,
                                "id": "suggestions-rejected",
                                "url": "/ru/LXDE/translate.html#filter=user-suggestions-rejected&user=admin"
                            },
                            {
                                "count": 34,
                                "id": "submissions-total",
                                "url": "/ru/LXDE/translate.html#filter=user-submissions&user=admin"
                            },
                            {
                                "count": 0,
                                "id": "submissions-overwritten",
                                "url": "/ru/LXDE/translate.html#filter=user-submissions-overwritten&user=admin"
                            }
                        ]
                    ]
                ]
            ]
        ],
        "username": "admin"
    }
