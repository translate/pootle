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

When starting Pootle with the :command:`pootle` runner script, by default it
will try to load custom settings from the :file:`~/.pootle/pootle.conf` file.
These settings will override the defaults set by Pootle.

An alternative location for the settings file can be specified by setting the
``-c </path/to/settings.conf/>`` flag when executing the runner. You can also
set the :envvar:`POOTLE_SETTINGS` environment variable to specify the path to
the custom configuration file. The environment variable will take precedence
over the command-line flag.

If instead of an installation you deployed Pootle straight from the git
repository, you can either set the :envvar:`POOTLE_SETTINGS` environment
variable or put a file under the :file:`pootle/settings/` directory. Note that
the files in this directory are read in alphabetical order, and **creating a
90-local.conf file is recommended** (files ending in *-local.conf* will be
ignored by git).


.. _settings#available:

Available Settings
------------------

This is a list of Pootle-specific settings grouped by the file they're
contained and ordered alphabetically.


10-base.conf
^^^^^^^^^^^^

This file contains base configuration settings.


.. setting:: POOTLE_INSTANCE_ID

``POOTLE_INSTANCE_ID``
  Instance ID. This is to differentiate multiple instances
  of the same app (e.g. development, staging and production).
  By default this value is exposed as a global <html> class name
  to allow overriding CSS rules based on the instance type.


.. setting:: POOTLE_TITLE

``POOTLE_TITLE``
  Default: ``'Pootle Translation Server'``

  The name of the Pootle server.


20-backends.conf
^^^^^^^^^^^^^^^^

Backend and caching settings.


.. setting:: POOTLE_CACHE_TIMEOUT

``POOTLE_CACHE_TIMEOUT``
  Default: ``604800`` (a week)

  .. versionadded:: 2.7

  Time in seconds to keep certain objects cached in memory (template fragments,
  language and project lists, permissions, etc.).

  Note that for anonymous users Pootle also uses :ref:`Django's caching
  middleware <django:the-per-site-cache>`, and its settings can be configured
  separately.


25-logging.conf
^^^^^^^^^^^^^^^

.. setting:: POOTLE_LOG_DIRECTORY

``POOTLE_LOG_DIRECTORY``
  Default: ``working_path('log')``

  .. versionadded:: 2.7

  The directory where Pootle writes event logs to. These are high-level
  logs of events on store/unit changes and manage.py commands executed


30-site.conf
^^^^^^^^^^^^

Site-specific settings.


.. setting:: POOTLE_CONTACT_ENABLED

``POOTLE_CONTACT_ENABLED``
  Default: ``True``

  Controls whether users will be able to use the contact form. The address to
  receive messages is controlled by :setting:`POOTLE_CONTACT_EMAIL`.


.. setting:: POOTLE_CONTACT_EMAIL

``POOTLE_CONTACT_EMAIL``
  Default: ``info@YOUR_DOMAIN.com``

  Address to receive messages sent through the contact form. This will only
  have effect if :setting:`POOTLE_CONTACT_ENABLED` is set to ``True``.


.. setting:: POOTLE_CONTACT_REPORT_EMAIL

``POOTLE_CONTACT_REPORT_EMAIL``
  Default: ``POOTLE_CONTACT_EMAIL``

  .. versionadded:: 2.7

  Email address to report errors on strings.


40-apps.conf
^^^^^^^^^^^^

Configuration settings for applications used by Pootle.


.. setting:: POOTLE_SIGNUP_ENABLED

``POOTLE_SIGNUP_ENABLED``
  Default: ``True``

  .. versionchanged:: 2.7

  Controls whether user sign ups are allowed or not. If set to ``False``,
  administrators will still be able to create new user accounts.


.. setting:: POOTLE_CUSTOM_TEMPLATE_CONTEXT

``POOTLE_CUSTOM_TEMPLATE_CONTEXT``
  Default: ``{}``

  .. versionchanged:: 2.7

  Custom template context dictionary. The values will be available in the
  templates as ``{{ custom.<key> }}``.


.. setting:: POOTLE_LEGALPAGE_NOCHECK_PREFIXES

``POOTLE_LEGALPAGE_NOCHECK_PREFIXES``
  Default: ``('/about', '/accounts', '/admin', '/contact', '/jsi18n', '/pages', )``

  .. versionchanged:: 2.7

  List of path prefixes where the ``LegalAgreementMiddleware`` will check
  if the current logged-in user has agreed all the legal documents defined
  for the Pootle instance. Don't change this unless you know what you're
  doing.

.. setting:: POOTLE_META_USERS

``POOTLE_META_USERS``
  Default: ``()``

  .. versionadded:: 2.7

  Additional meta, or non-human, accounts. Pootle already manages the 'system'
  and 'nobody' users who own system updates to translations and submissions by
  anonymous users.  These meta accounts have their own simple public profiles
  and won't track scores.


.. setting:: POOTLE_MARKUP_FILTER

``POOTLE_MARKUP_FILTER``
  Default: ``(None, {})``

  Two-tuple defining the markup filter to apply in certain textareas.

  - Accepted values for the first element are ``textile``, ``markdown``,
    ``restructuredtext`` and None

  - The second element should be a dictionary of keyword arguments that
    will be passed to the markup function

  Examples::

    POOTLE_MARKUP_FILTER = (None, {})

    POOTLE_MARKUP_FILTER = ('markdown', {'safe_mode': 'escape'})

    POOTLE_MARKUP_FILTER = ('restructuredtext', {
                                'settings_overrides': {
                                    'report_level': 'quiet',
                                 }
                            })


.. setting:: POOTLE_CAPTCHA_ENABLED

``POOTLE_CAPTCHA_ENABLED``
  Default: ``True``

  Enable spam prevention through a captcha.


.. setting:: POOTLE_REPORTS_MARK_FUNC

``POOTLE_REPORTS_MARK_FUNC``
  Default: ``''`` (empty string)

  .. versionadded:: 2.7

  The graph of a user's activity, within reports, can be `marked
  <https://code.google.com/archive/p/flot-marks/>`_  to indicate events by
  using this function. The setting must contain an import path to such a
  marking function (string).

  The function receives the user and graph ranges and returns an array of
  applicable marks.

  Parameters:

  - ``username`` - user for whom we're producing this graph
  - ``start`` (datetime) - start date of the graph
  - ``end`` (datetime) - end date of the graph

  The function must return an **array of dictionaries** (marks), where
  every mark has the following properties:

  - ``position``, specifying the point in the x-axis where the mark should
    be set (UNIX timestamp multiplied by 1000), and
  - ``label`` specifying the text that will be displayed next to the mark.


.. setting:: POOTLE_SCORE_COEFFICIENTS

``POOTLE_SCORE_COEFFICIENTS``
  Default::

    {
        'EDIT': 5.0/7,
        'REVIEW': 2.0/7,
        'SUGGEST': 0.2,
        'ANALYZE': 0.1,
    }

  .. versionadded:: 2.7.3

  Parameters:

  - ``EDIT`` - coefficient to calculate an user score change for
    edit actions.
  - ``REVIEW`` - coefficient to calculate an user score change for
    review actions.
  - ``SUGGEST`` - coefficient to calculate an user score change for
    new suggestions.
  - ``ANALYZE`` - coefficient to calculate an user score change for
    rejecting suggestions and penalty for the rejected suggestion.


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


.. setting:: POOTLE_SYNC_FILE_MODE

``POOTLE_SYNC_FILE_MODE``
  Default: ``0644``

  .. versionchanged:: 2.7

  On POSIX systems, files synchronized to disk will be assigned this permission.
  Use ``0644`` for publically-readable files or ``0600`` if you want only the
  Pootle user to be able to read them.


.. setting:: POOTLE_TM_SERVER

``POOTLE_TM_SERVER``
  .. versionadded:: 2.7

  .. versionchanged:: 2.7.3

     Added the :setting:`WEIGHT <POOTLE_TM_SERVER-WEIGHT>` and
     :setting:`MIN_SIMILARITY <POOTLE_TM_SERVER-MIN_SIMILARITY>` options. Also
     added another default TM used to import external translations from files.


  Default: ``{}`` (empty dict)

  Example configuration for local/external TM server:

  .. code-block:: python

    {
        'local': {
            'ENGINE': 'pootle.core.search.backends.ElasticSearchBackend',
            'HOST': 'localhost',
            'PORT': 9200,
            'INDEX_NAME': 'translations',
            'WEIGHT': 1,
        },
        'external': {
            'ENGINE': 'pootle.core.search.backends.ElasticSearchBackend',
            'HOST': 'localhost',
            'PORT': 9200,
            'INDEX_NAME': 'external-translations',
            'WEIGHT': 0.9,
        },
    }


  This is configured to access a standard Elasticsearch setup.  Change the
  settings for any non-standard setup.  Change ``HOST`` and ``PORT`` settings
  as required.

  The default ``local`` TM is automatically updated every time a new
  translation is submitted. The other TMs are not automatically updated so they
  can be trusted to provide selected high quality translations.

  .. setting:: POOTLE_TM_SERVER-INDEX_NAME

  Every TM server must have its own unique ``INDEX_NAME``.

  .. setting:: POOTLE_TM_SERVER-WEIGHT

  ``WEIGHT`` provides a weighting factor to alter the final score for TM
  results from this TM server. Valid values are between ``0.0`` and ``1.0``,
  both included. Defaults to ``1.0`` if not provided.

  .. setting:: POOTLE_TM_SERVER-MIN_SIMILARITY

  ``MIN_SIMILARITY`` serves as a threshold value to filter out results that are
  potentially too far from the source text. The Levenshtein distance is
  considered when measuring how similar the text is from the source text, and
  this represents a real value in the (0..1) range, 1 being 100% similarity.
  The default value (0.7) should work fine in most cases, although your mileage
  might vary.


.. setting:: POOTLE_MT_BACKENDS

``POOTLE_MT_BACKENDS``
  Default: ``[]`` (empty list)

  This setting enables translation suggestions through several online services.

  The elements for the list are two-element tuples containing the name of the
  service and an optional API key.

  Available options are:

  ``GOOGLE_TRANSLATE``: Google Translate service.
    For this service you need to obtain an API key. Note that Google Translate
    API is a `paid service <https://cloud.google.com/translate/v2/pricing>`_.

  ``YANDEX_TRANSLATE``: Yandex.Translate service.
    For this service you need to `obtain a Yandex API key
    <https://tech.yandex.com/keys/get/?service=trnsl>`_.

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


.. setting:: POOTLE_TRANSLATION_DIRECTORY

``POOTLE_TRANSLATION_DIRECTORY``
  Default: ``working_path('translations')``

  The directory where projects hosted on Pootle store their translation files.
  :djadmin:`sync_stores` will write to this directory and
  :djadmin:`update_stores` will read from this directory.


.. setting:: POOTLE_QUALITY_CHECKER

``POOTLE_QUALITY_CHECKER``
  Default: ``''``

  .. versionadded:: 2.7

  The import path to a class that provides alternate quality checks to
  Pootle.  If it is unset then the Translate Toolkit checking functions are
  used and you can make adjustments in the project's admin page.  If set
  then the quality checker function is used for all projects.

  .. note:: If set, only the checker function defined here is used instead of
     the Translate Toolkit counterparts. Both cannot be selectively applied.


.. setting:: POOTLE_WORDCOUNT_FUNC

``POOTLE_WORDCOUNT_FUNC``
  Default: ``translate.storage.statsdb.wordcount``

  .. versionadded:: 2.7

  The import path to a function that provides wordcounts for Pootle.

  Current options:

  - Translate Toolkit (default) - translate.storage.statsdb.wordcount
  - Pootle - pootle.core.utils.wordcount.wordcount

  Adding a custom function allows you to alter how words are counted.

  .. warning:: Changing this function requires that you run
     :djadmin:`refresh_stats --calculate-wordcount <refresh_stats>` to
     recalculate the associated wordcounts.


.. _settings#deprecated:

Deprecated Settings
-------------------

.. setting:: ENABLE_ALT_SRC

``ENABLE_ALT_SRC``
  .. deprecated:: 2.5
     Alternate source languages are now on by default. This ensures
     that translators have access to as much useful information as possible
     when translating.


.. setting:: POOTLE_TOP_STATS_CACHE_TIMEOUT

``POOTLE_TOP_STATS_CACHE_TIMEOUT``
  .. deprecated:: 2.7
     The overview page statistics rewrite has removed these statistics and the
     RQ based statistics has also removed the load of this type of data so this
     setting has been removed.


.. setting:: VCS_DIRECTORY

``VCS_DIRECTORY``
  .. deprecated:: 2.7
     Version Control Support has been removed from Pootle.  We feel we can
     support version control better in future.  You can currently make use of
     :djadmin:`sync_stores` and :djadmin:`update_stores` to automate your own
     integration.


.. setting:: CONTRIBUTORS_EXCLUDED_NAMES

``CONTRIBUTORS_EXCLUDED_NAMES``
  .. deprecated:: 2.7
     The contributors page has been removed and is being replaced with better
     user statistics.


.. setting:: CONTRIBUTORS_EXCLUDED_PROJECT_NAMES

``CONTRIBUTORS_EXCLUDED_PROJECT_NAMES``
  .. deprecated:: 2.7
     The contributors page has been removed and is being replaced with better
     user statistics.


.. setting:: MIN_AUTOTERMS

``MIN_AUTOTERMS``
  .. deprecated:: 2.7
     Terminology auto-extraction feature has been removed.


.. setting:: MAX_AUTOTERMS

``MAX_AUTOTERMS``
  .. deprecated:: 2.7
     Terminology auto-extraction feature has been removed.


.. setting:: DESCRIPTION

``DESCRIPTION``
  .. deprecated:: 2.7
     Pootle no longer displays site description on the landing page, but rather
     makes use of static pages to convey information to users in the sidebar.
     Use :doc:`static pages </features/staticpages>` and :doc:`customization
     </developers/customization>` if you want to give users information about
     the Pootle site.


.. setting:: FUZZY_MATCH_MAX_LENGTH

``FUZZY_MATCH_MAX_LENGTH``
  .. deprecated:: 2.7
     Update against templates feature has been removed.


.. setting:: FUZZY_MATCH_MIN_SIMILARITY

``FUZZY_MATCH_MIN_SIMILARITY``
  .. deprecated:: 2.7
     Update against templates feature has been removed.


.. setting:: EXPORTED_DIRECTORY_MODE

``EXPORTED_DIRECTORY_MODE``
  .. deprecated:: 2.7
     Offline translation support was rewritten and the setting was unused.
