.. _authentication:

Authentication backends
=======================

.. _authentication#ldap:

LDAP authentication
-------------------

The different elements of the LDAP configuration are defined in your
:file:`settings/51-ldap.conf` and :file:`settings/50-project.conf` files.
Although most of it is explained in the settings files, below
is a brief example of a working configuration.

The mail addresses are *john.doe@website.org*, the LDAP server is
*your.ldapserver.org*. In this case, we need a specific user account to search
in our LDAP server, this user/password is *admin*/*pootle*. The LDAP accounts
are based on the mail addresses: these are the uids. Finally, *John Doe* is
part of the branch *employees* on the LDAP.

:file:`settings/50-project.conf`::

    # Authenticate first with an LDAP system and then fall back to Django's
    # authentication system.
    AUTHENTICATION_BACKENDS = [
        #: Uncomment the following line for enabling LDAP authentication
        'pootle.auth.ldap_backend.LdapBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]

:file:`settings/51-ldap.conf`::

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
