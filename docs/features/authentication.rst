.. _authentication:

Authentication Backends
=======================

.. _authentication#social:

Social Authentication
---------------------

Pootle uses Django-Allauth for authentication, which supports several social
authentication backends. By default, support for OpenID as well as
`Persona <https://www.mozilla.org/en-US/persona/>`_ is enabled with no further
configuration requirements.

Support for various OAuth and OAuth2 backends, such as Google and Facebook, can
be enabled. For a full list of providers and additional settings, refer to the
`Allauth documentation <https://github.com/pennersr/django-allauth#supported-providers>`_.
