.. _using-pootle-api:

Using Pootle API
****************

In order to use the Pootle API it is necessary to know how some things, like the
supported formats, available authentication methods or basic rules for
performing queries.

Pootle API is created using `Tastypie <http://tastypieapi.org/>`_ so you might
need to refer to `its documentation <http://django-tastypie.readthedocs.org/>`_
as well.


.. _using-pootle-api#how-to-perform-queries:

How to perform API queries
==========================

The structure of the API URLs is ``<SERVER>/api/<API_VERSION>/<QUERY>`` where:

+---------------+-------------------------------+
| Placeholder   | Description                   |
+===============+===============================+
| <SERVER>      | The URL of the Pootle server  |
+---------------+-------------------------------+
| <API_VERSION> | Version number of the API     |
+---------------+-------------------------------+
| <QUERY>       | Resource query URI            |
+---------------+-------------------------------+

So the API can be queried using URLs like::

  http://pootle.locamotion.org/api/v1/translation-projects/65/


.. _using-pootle-api#list-matching-a-criteria:

List matching a criteria
------------------------

For some resources it is also possible to narrow down the list by providing a
:wp:`query string <Query_string>` containing filters `provided by Tastypie
<http://django-tastypie.readthedocs.org/en/latest/resources.html#basic-filtering>`_
(that actually are `Django ORM Field Lookups
<https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups>`_).

In this case the structure of the API URLs is
``<SERVER>/api/<API_VERSION>/<RESOURCE>/?<CRITERIA>`` where ``<CRITERIA>`` is
the query string. For example::

  http://pootle.locamotion.org/api/v1/units/?mtime__month=05&mtime__day=12&state__exact=200


.. _using-pootle-api#authentication:

Authentication
==============

Pootle requires authentication for accessing its API.

The method used for authentication is :wp:`HTTP Basic Authentication
<Basic_access_authentication>` which requires providing a username and a
password (the same ones used for Pootle login).

.. note:: Other authentication methods can be added in the future.


.. _using-pootle-api#authorization:

Authorization
=============

The Pootle API allows to interact with resources that represent some of the
data handled internally by Pootle. In order to avoid all users access or alter
data they are not meant to, the Pootle API checks if the visitor has enough
permissions to perform the requested actions on the resources. The permissions
used for these checks are the same permissions used in Pootle for regular
users.

For some particular resources some other checks can be done to allow or deny
performing the requested action. For example the visitors can only see the
:ref:`User resource <api-user-resources>` for the user that they used to log
in the Pootle API.


.. _using-pootle-api#formats:

Formats
=======

By default Pootle API returns only :wp:`JSON` replies. It is possible to use all
the :ref:`formats supported <tastypie:settings.TASTYPIE_DEFAULT_FORMATS>` by
Tastypie.


.. _using-pootle-api#tools-libraries:

Tools and libraries
===================

Translate is currently developing a `client for Pootle API
<https://github.com/translate/pootle-client>`_, but there are several other
:ref:`libraries and programs <tastypie:ref-tools>` capable of interacting with
Pootle API. For example here is an example script that uses `Slumber
<http://slumber.readthedocs.org/>`_ to retrieve and print the list of used
languages in Pootle:

.. code-block:: python

  import slumber

  # Change the following to match your Pootle URL, your username and password.
  API_URL = "http://127.0.0.1:8000/api/v1/"
  AUTH=('admin', 'admin')

  api = slumber.API(API_URL, auth=AUTH)

  # Get all languages data.
  lang_data = api.languages.get()

  for lang in lang_data["objects"]:
      print(lang["code"])


.. note:: Remember to `install Slumber <http://slumber.readthedocs.org/>`_ in
   order to run the previous code.
