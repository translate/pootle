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


.. setting:: TITLE

``TITLE``
  The name of the Pootle server.


.. setting:: POOTLE_INSTANCE_ID

``POOTLE_INSTANCE_ID``
  Instance ID. This is to differentiate multiple instances
  of the same app (e.g. development, staging and production).
  By default this value is exposed as a global <html> class name
  to allow overriding CSS rules based on the instance type.


20-backends.conf
^^^^^^^^^^^^^^^^

Backend and caching settings.


.. setting:: OBJECT_CACHE_TIMEOUT

``OBJECT_CACHE_TIMEOUT``
  Default: ``2500000``

  Time in seconds the Pootle's statistics cache will last.


.. setting:: POOTLE_LOG_DIRECTORY

``POOTLE_LOG_DIRECTORY``
  Default: ``/var/log/pootle/``

  The directory where Pootle writes event logs to. These are high-level
  logs of events on store/unit changes and manage.py commands executed


30-site.conf
^^^^^^^^^^^^

Site-specific settings.


.. setting:: CAN_CONTACT

``CAN_CONTACT``
  Default: ``True``

  Controls whether users will be able to use the contact form. The address to
  receive messages is controlled by :setting:`CONTACT_EMAIL`.


.. setting:: CONTACT_EMAIL

``CONTACT_EMAIL``
  Default: ``info@YOUR_DOMAIN.com``

  Address to receive messages sent through the contact form. This will only
  have effect if :setting:`CAN_CONTACT` is set to ``True``.


.. setting:: POOTLE_REPORT_STRING_ERRORS_EMAIL

``POOTLE_CONTACT_REPORT_EMAIL``
  Default: ``CONTACT_EMAIL``

  .. versionadded:: 2.7

  Email address to report errors on strings.


40-apps.conf
^^^^^^^^^^^^

Configuration settings for applications used by Pootle.


.. setting:: CAN_REGISTER

``CAN_REGISTER``
  Default: ``True``

  Controls whether user registrations are allowed or not. If set to ``False``,
  administrators will still be able to create new user accounts.


.. setting:: CUSTOM_TEMPLATE_CONTEXT

``CUSTOM_TEMPLATE_CONTEXT``
  Default: ``{}``

  .. versionadded:: 2.5

  Custom template context dictionary. The values will be available in the
  templates as ``{{ custom.<key> }}``.


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


.. setting:: LEGALPAGE_NOCHECK_PREFIXES

``LEGALPAGE_NOCHECK_PREFIXES``
  Default: ``('/accounts', '/admin', '/contact', '/jsi18n', '/pages', )``

  .. versionadded:: 2.5.1

  List of path prefixes where the ``LegalAgreementMiddleware`` will check
  if the current logged-in user has agreed all the legal documents defined
  for the Pootle instance. Don't change this unless you know what you're
  doing.

.. setting:: POOTLE_META_USERS

``POOTLE_META_USERS``
  Default: ``()``

  List of special 'API users'.


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


.. setting:: USE_CAPTCHA

``USE_CAPTCHA``
  Default: ``True``

  Enable spam prevention through a captcha.


60-translation.conf
^^^^^^^^^^^^^^^^^^^

Translation environment configuration settings.

.. setting:: AMAGAMA_URL

``AMAGAMA_URL``
  Default: ``https://amagama-live.translatehouse.org/api/v1/``

  URL to an amaGama Translation Memory server. The default service should work
  fine, but if you have a custom server set it here.

  This URL must point to the public API URL which returns JSON. Don't forget
  the trailing slash.


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


.. _settings#deprecated:

Deprecated Settings
-------------------

.. setting:: ENABLE_ALT_SRC

``ENABLE_ALT_SRC``
  Default: ``True``

  .. deprecated:: 2.5
     Alternate source languages are now on by default. This ensures
     that translators have access to as much useful information as possible
     when translating.

  Display alternate source languages in the translation interface.
