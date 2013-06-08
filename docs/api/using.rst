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


.. _using-pootle-api#authentication:

Authentication
==============

Pootle API requires authentication for accessing its API.

The method used for authentication is :wp:`HTTP Basic Authentication
<Basic_access_authentication>` which requires providing a username and a
password (the same ones used for Pootle login).

Also it is necessary that the user has enough permissions to access the
resources. The permissions used to perform this check are the same permissions
used in Pootle.

.. note:: Other authentication methods can be added in the future.


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
