.. _settings:

Settings
========

You will find all the Pootle-specific settings in this document.

If you have upgraded, you might want to compare your previous copy to the one
distributed with the Pootle version for any new settings you might be interested
in.


.. _settings#customizing:

Customizing Settings
--------------------

When starting Pootle with the ``pootle`` runner script, by default it will try
to load custom settings from the *~/.pootle/pootle.conf* file. These settings
will override the defaults set by Pootle.

An alternative location for the settings file can be specified by setting the
``-c </path/to/settings.conf/>`` flag when executing the runner. You can also
set the ``POOTLE_SETTINGS`` environment variable to specify the path to the
custom configuration file. The environment variable will take precedence over
the command-line flag.

If instead of an installation you deployed Pootle straight from the git
repository, you can either set the ``POOTLE_SETTINGS`` environment variable or
put a file under the *pootle/settings/* directory. Note that the files in this
directory are read in alphabetical order, and  **creating a 90-local.conf file
is recommended** (files ending in *-local.conf* will be ignored by git).


.. _settings#available:

Available Settings
------------------

This is a list of Pootle-specific settings grouped by the file they're
contained and ordered alphabetically.


10-base.conf
^^^^^^^^^^^^

This file contains base configuration settings.


.. setting:: DESCRIPTION

``DESCRIPTION``
  Description of the Pootle server.


.. setting:: TITLE

``TITLE``
  The name of the Pootle server.


20-backends.conf
^^^^^^^^^^^^^^^^

Backend and caching settings.


.. setting:: OBJECT_CACHE_TIMEOUT

``OBJECT_CACHE_TIMEOUT``
  Default: ``2500000``

  Time in seconds the Pootle's statistics cache will last.


30-site.conf
^^^^^^^^^^^^

Site-specific settings.


.. setting:: CAN_CONTACT

``CAN_CONTACT``
  Default: ``True``

  Controls whether users will be able to use the contact form. The address to
  receive messages is controlled by :setting:`CONTACT_EMAIL`.


.. setting:: CAN_REGISTER

``CAN_REGISTER``
  Default: ``True``

  Controls whether user registrations are allowed or not. If set to ``False``,
  administrators will still be able to create new user accounts.


.. setting:: CONTACT_EMAIL

``CONTACT_EMAIL``
  Default: ``info@YOUR_DOMAIN.com``

  Address to receive messages sent through the contact form. This will only
  have effect if :setting:`CAN_CONTACT` is set to ``True``.


40-apps.conf
^^^^^^^^^^^^

Configuration settings for applications used by Pootle.


.. setting:: API_LIMIT_PER_PAGE

``API_LIMIT_PER_PAGE``
  Default: ``0``

  .. versionadded:: 2.5.1

  Number of records Pootle API will show in a list view. ``0`` means no limit.


.. setting:: CUSTOM_TEMPLATE_CONTEXT

``CUSTOM_TEMPLATE_CONTEXT``
  Default: ``{}``

  .. versionadded:: 2.5

  Custom template context dictionary. The values will be available in the
  templates as ``{{ custom.<key> }}``.


.. setting:: EMAIL_SEND_HTML

``EMAIL_SEND_HTML``
  Default: ``False``

  By default Pootle sends only text emails. If your organization would prefer
  to send mixed HTML/TEXT emails, set this to ``True``, and update
  *activation_email.txt* and *activation_email.html* in the
  *templates/registration/* directory.

  .. note::

    Password reset emails will still be sent in plain text. This is a limitation
    of the underlying system.


.. setting:: FUZZY_MATCH_MAX_LENGTH

``FUZZY_MATCH_MAX_LENGTH``
  Default: ``70``

  .. versionadded:: 2.5

  Maximum character length to consider when doing fuzzy matching. The default
  might not be enough for long texts. Please note this affects all fuzzy
  matching operations, so bear in mind this might affect performance.


.. setting:: FUZZY_MATCH_MIN_SIMILARITY

``FUZZY_MATCH_MIN_SIMILARITY``
  Default: ``75``

  .. versionadded:: 2.5

  Minimum similarity to consider when doing fuzzy matching. Please note this
  affects all fuzzy matching operations, so bear in mind this might affect
  performance.


.. setting:: MIN_AUTOTERMS

``MIN_AUTOTERMS``
  Default: ``60``

  When building the terminology, the minimum number of terms that will be
  automatically extracted.


.. setting:: MARKUP_FILTER

``MARKUP_FILTER``
  Default: ``(None, {})``

  .. versionadded:: 2.5

  Two-tuple defining the markup filter to apply in certain textareas.

  - Accepted values for the first element are ``textile``, ``markdown``,
    ``restructuredtext`` and None

  - The second element should be a dictionary of keyword arguments that
    will be passed to the markup function

  Examples::

    MARKUP_FILTER = (None, {})

    MARKUP_FILTER = ('markdown', {'safe_mode': 'escape'})

    MARKUP_FILTER = ('restructuredtext', {'settings_overrides': {
                                             'report_level': 'quiet',
                                             }
                                         })


.. setting:: MAX_AUTOTERMS

``MAX_AUTOTERMS``
  Default: ``600``

  When building the terminology, the maximum number of terms that will be
  automatically extracted.


.. setting:: TASTYPIE_DEFAULT_FORMATS

``TASTYPIE_DEFAULT_FORMATS``
  Default: ``['json']``

  .. versionadded:: 2.5.1

  List defining the allowed serialization formats for Pootle API. Check
  :ref:`Tastypie docs <tastypie:settings.TASTYPIE_DEFAULT_FORMATS>` for all the
  available formats and :ref:`its dependencies <tastypie:ref-tutorial>` (see in
  Installation section).


.. setting:: TOPSTAT_SIZE

``TOPSTAT_SIZE``
  Default: ``5``

  The number of rows displayed in the top contributors table.


.. setting:: USE_CAPTCHA

``USE_CAPTCHA``
  Default: ``True``

  Enable spam prevention through a captcha.


.. _settings#ldap:

51-ldap.conf
^^^^^^^^^^^^

Optional LDAP configuration settings. To enable the LDAP authentication
backend, you'll need to append ``'pootle.auth.ldap_backend.LdapBackend'`` to
the list of ``AUTHENTICATION_BACKENDS``.


.. setting:: AUTH_LDAP_ANON_DN

``AUTH_LDAP_ANON_DN``
  Default: ``''``

  Anonymous credentials: Distinguished Name.


.. setting:: AUTH_LDAP_ANON_PASS

``AUTH_LDAP_ANON_PASS``
  Default: ``''``

  Anonymous credentials: password.


.. setting:: AUTH_LDAP_BASE_DN

``AUTH_LDAP_BASE_DN``
  Default: ``''``

  Base DN to search


.. setting:: AUTH_LDAP_FIELDS

``AUTH_LDAP_FIELDS``
  Default: ``{'dn': 'dn'}``

  A mapping of Pootle field names to LDAP fields.  The key is Pootle's name,
  the value should be your LDAP field name.  If you don't use the field or
  don't want to automatically retrieve these fields from LDAP comment them out.
  The only required field is ``dn``.


.. setting:: AUTH_LDAP_FILTER

``AUTH_LDAP_FILTER``
  Default: ``''``

  What are we filtering on? %s will be the username, for example ``'sn=%s'``,
  or ``'uid=%s'``.


.. setting:: AUTH_LDAP_SERVER

``AUTH_LDAP_SERVER``
  Default: ``''``

  The LDAP server. Format: ``protocol://hostname:port``


60-translation.conf
^^^^^^^^^^^^^^^^^^^

Translation environment configuration settings.

.. setting:: AMAGAMA_URL

``AMAGAMA_URL``
  Default: ``http://amagama.locamotion.org/tmserver/``

  URL to an amaGama Translation Memory server. The default service should work
  fine, but if you have a custom server set it here.

  This URL must point to the public API URL which returns JSON. Don't forget
  the trailing slash.


.. setting:: AUTOSYNC

``AUTOSYNC``
  Default: ``False``

  Set this to ``True`` if you want translation files to be updated
  immediatly.

  .. note::

    This negatively affects performance and should be avoided unless another
    application needs direct access to the files.

  .. warning::

    This feature is not maintained anymore, use it at your own risk.


.. setting:: EXPORTED_DIRECTORY_MODE

``EXPORTED_DIRECTORY_MODE``
  Default: ``0755``

  On POSIX systems, exported directories will be assigned this permission. Use
  ``0755`` for publically-readable directories or ``0700`` if you want only the
  Pootle user to be able to read them.


.. setting:: EXPORTED_FILE_MODE

``EXPORTED_FILE_MODE``
  Default: ``0644``

  On POSIX systems, exported files will be assigned this permission. Use
  ``0644`` for publically-readable files or ``0600`` if you want only the
  Pootle user to be able to read them.


.. setting:: LIVE_TRANSLATION

``LIVE_TRANSLATION``
  Default: ``False``

  Live translation means that the project called *Pootle* is used to provide
  the localized versions of Pootle. Set this to ``True`` to enable live
  translation of Pootle's UI. This is a good way to learn how to use Pootle,
  but it has high impact on performance.


.. setting:: LOOKUP_BACKENDS

``LOOKUP_BACKENDS``
  Default: ``['wikipedia']`` (Wikipedia enabled)

  Enables backends for web-based lookups.

  Available options: ``wikipedia``.


.. setting:: MT_BACKENDS

``MT_BACKENDS``
  Default: ``[]`` (empty list)

  This setting enables translation suggestions through several online services.

  The elements for the list are two-element tuples containing the name of the
  service and an optional API key.

  Available options are:

  ``APERTIUM``: Apertium service.
    For this service you need to set the API key. Get your key at
    http://api.apertium.org/register.jsp

  ``GOOGLE_TRANSLATE``: Google Translate service.
    For this service you need to set the API key. Note that Google Translate
    API is a paid service. See more at
    https://developers.google.com/translate/v2/pricing 


.. setting:: PARSE_POOL_CULL_FREQUENCY

``PARSE_POOL_CULL_FREQUENCY``
  Default: ``4``

  When the pool fills up, 1/PARSE_POOL_CULL_FREQUENCY number of files will be
  removed from the pool.


.. setting:: PARSE_POOL_SIZE

``PARSE_POOL_SIZE``
  Default: ``40``

  To avoid rereading and reparsing translation files from disk on
  every request, Pootle keeps a pool of already parsed files in memory.

  Larger pools will offer better performance, but higher memory usage
  (per server process).


.. setting:: PODIRECTORY

``PODIRECTORY``
  Default: ``working_path('po')``

  The directory where the translation files are kept.


.. setting:: VCS_DIRECTORY

``VCS_DIRECTORY``
  Default: ``working_path('repos')``

  .. versionadded:: 2.5

  The directory where version control clones/checkouts are kept.


.. _settings#deprecated:

Deprecated Settings
-------------------

.. setting:: ENABLE_ALT_SRC

``ENABLE_ALT_SRC``
  Defaut: ``True``

  .. deprecated:: 2.5
     Alternate source languages are now on by default. This ensures
     that translators have access to as much useful information as possible
     when translating.

  Display alternate source languages in the translation interface.
