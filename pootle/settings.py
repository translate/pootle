#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""This is a standard module defining some Django settings, as well as some
settings specific to Pootle.

Note that some of this can also be specified in pootle.ini in order to have a
configuration override outside of the code."""

import logging
import os

from pootle.install_dirs import *

INTERNAL_IPS = ('127.0.0.1',)
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# dummy translate function so we can extract text
_ = lambda x : x

TITLE = _("Pootle Demo")

#l10n: Change the language code (en) to your language code, and replace ltr with rtl if you language is written from right to left.
DESCRIPTION = _("""<div dir="ltr" lang="en">
<h2 class="title">This is a demo installation of Pootle.</h2>
<p class="about">You can also visit the official <a href="http://pootle.locamotion.org">Pootle server</a>. The server administrator has not provided contact information or a description of this server. If you are the administrator for this server, edit this description in your preference file or in the administration interface.</p>
</div>""")

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Africa/Johannesburg'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = data_path('html')+'/'
# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/html/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
# TODO: We should find a way to reset this for new installations.
SECRET_KEY = '^&4$dlpce2_pnronsi289xd7-9ke10q_%wa@9srm@zaa!ig@1k'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    # Uncomment to use pagecahing
    'pootle_misc.middleware.baseurl.BaseUrlMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'pootle_misc.middleware.siteconfig.SiteConfigMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware', # THIS MUST BE FIRST
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'pootle_misc.middleware.errorpages.ErrorPagesMiddleware',
    'django.middleware.common.CommonMiddleware',
    'pootle.middleware.check_cookies.CheckCookieMiddleware',
    'pootle.middleware.captcha.CaptchaMiddleware',
    #'pootle.middleware.profile.ProfilerMiddleware',
    # Uncomment to use pagecaching
    'django.middleware.cache.FetchFromCacheMiddleware' # THIS MUST BE LAST
)

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

ROOT_URLCONF = 'pootle.urls'

TEMPLATE_CONTEXT_PROCESSORS = ("django.core.context_processors.auth",
                               "django.core.context_processors.i18n",
                               "django.core.context_processors.media",
                               "django.core.context_processors.request",
                               "pootle_misc.context_processors.pootle_context")

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    data_path('templates'),
)

INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.admin',
    'pootle_app',
    'pootle_misc',
    'pootle_store',
    'pootle_language',
    'pootle_project',
    'pootle_translationproject',
    'pootle_profile',
    'pootle_statistics',
    'pootle_notifications',
    'pootle_autonotices',
    'pootle_terminology',
    'registration',
    'profiles',
    'djblets.siteconfig',
    'djblets.util',
)

AUTH_PROFILE_MODULE = "pootle_profile.PootleProfile"

ENABLE_ALT_SRC = True

# number of rows in top contributors table
TOPSTAT_SIZE = 5

# django-registration configs
ACCOUNT_ACTIVATION_DAYS = 10

# keep stats cache for roughly a month
OBJECT_CACHE_TIMEOUT = 2500000

execfile(config_path("localsettings.py"))

if LIVE_TRANSLATION:
    # Look for localization files under PODIRECTORY/pootle
    LOCALE_PATHS = (os.path.join(PODIRECTORY, "pootle"), )
else:
    # look for localization files under mo directory
    LOCALE_PATHS = (data_path("mo"), )

from pootle.i18n import override, gettext_live, gettext
from django.utils import translation
from django.utils.translation import trans_real

LANGUAGES = override.find_languages(LOCALE_PATHS[0])

def hijack_translation():
    """sabotage django's fascist linguistical regime"""
    # override functions that check if language if language is
    # known to Django
    translation.check_for_language = lambda lang_code: True
    trans_real.check_for_language = lambda lang_code: True
    translation.get_language_from_request = override.get_language_from_request

    # override django's inadequate bidi detection
    translation.get_language_bidi = override.get_language_bidi

    if LIVE_TRANSLATION:
        trans_real.translation = override.translation_dummy
        override.override_gettext(gettext_live)
    else:
        # even when live translation is not enabled we hijack
        # gettext functions to install the safe variable
        # formatting override
        override.override_gettext(gettext)

hijack_translation()


# setup a tempdir inside the PODIRECTORY heirarchy, this way we have
# reasonable guarantee that temp files will be created on the same
# filesystem as translation files (required for save operations).
import tempfile
tempfile.tempdir = os.path.join(PODIRECTORY, ".tmp")
# ensure that temp dir exists
if not os.path.exists(tempfile.tempdir):
    os.mkdir(tempfile.tempdir)

TEMPLATE_DEBUG = DEBUG
if TEMPLATE_DEBUG:
    TEMPLATE_CONTEXT_PROCESSORS += ("django.core.context_processors.debug",)

if DEBUG:
    logging.basicConfig(
            level = logging.DEBUG,
            format =  '%(asctime)s %(levelname)s %(message)s',
            )
else:
    # Will log only CRITICAL errors to the console
    logging.basicConfig(
            level = logging.INFO,
            format =  '%(asctime)s %(levelname)s %(message)s',
            )


# cache template loading to reduce IO strain
if not DEBUG:
    template_cache = {}
    def cache_templates(f):
        def decorated_f(template_name):
            if template_name not in template_cache:
                template_cache[template_name] = f(template_name)
            return template_cache[template_name]
        return decorated_f

    from django.template import loader
    loader.get_template = cache_templates(loader.get_template)
