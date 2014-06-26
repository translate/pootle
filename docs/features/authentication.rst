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

.. _authentication#ldap:

LDAP Authentication
-------------------

LDAP configuration can be enabled by appending the
``'pootle.core.auth.ldap_backend.LdapBackend'`` to the list of
:setting:`AUTHENTICATION_BACKENDS`. The settings page lists all the
:ref:`configuration keys available for LDAP <settings#ldap>`.

Below a brief example of a working configuration is showcased.

The mail addresses are *john.doe@website.org*, the LDAP server is
*your.ldapserver.org*. In this case, we need a specific user account to search
in our LDAP server, this user/password is *admin*/*pootle*. The LDAP accounts
are based on the mail addresses: these are the uids. Finally, *John Doe* is
part of the branch *employees* on the LDAP.

.. code-block:: python

    # Authenticate first with an LDAP system and then fall back to Django's
    # authentication system.
    AUTHENTICATION_BACKENDS = [
        #: Uncomment the following line for enabling LDAP authentication
        'pootle.core.auth.ldap_backend.LdapBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]

    # The LDAP server.  Format:  protocol://hostname:port
    AUTH_LDAP_SERVER = 'ldap://your.ldapserver.org:389'
    # Anonymous Credentials : if you don't have a super user, don't put cn=...
    AUTH_LDAP_ANON_DN = 'cn=admin,dc=website,dc=org'
    AUTH_LDAP_ANON_PASS = 'pootle'
    # Base DN to search
    AUTH_LDAP_BASE_DN = 'ou=employees,dc=website,dc=org'
    # What are we filtering on?  %s will be the username (must be in the string)
    # In this case, we filter on mails, which are the uid.
    AUTH_LDAP_FILTER = 'uid=%s'

    # This is a mapping of Pootle field names to LDAP fields.  The key is
    # Pootle's name, the value should be your LDAP field name.  If you don't use the
    # field or don't want to automatically retrieve these fields from LDAP comment
    # them out. The only required field is 'dn'. givenName, sn and uid are the names
    # of the LDAP fields.
    AUTH_LDAP_FIELDS = {
            'dn': 'dn',
            'first_name':'givenName',
            'last_name':'sn',
            'email':'uid'
    }
