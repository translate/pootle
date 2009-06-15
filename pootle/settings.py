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

import syspath_override
import os

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

import logging
from ConfigParser import ConfigParser

def pootle_home(filename):
    return os.path.join(ROOT_DIR, filename)

DEBUG = True
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1',)
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS


TITLE = "Pootle Demo"
DESCRIPTION = """<div dir="ltr" lang="en">This is a demo installation of Pootle.<br /> You can also visit the official <a href="http://pootle.locamotion.org">Pootle server</a>. The server administrator has not provided contact information or a description of this server. If you are the administrator for this server, edit this description in your preference file or in the administration interface.</div>"""

#Example for google as an external smtp server
#DEFAULT_FROM_EMAIL = 'DEFAULT_USER@YOUR_DOMAIN.com'
#EMAIL_HOST_USER = 'USER@YOUR_DOMAIN.com'
#EMAIL_HOST_PASSWORD = 'YOUR_PASSWORD'
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_PORT = 587
#EMAIL_USE_TLS = True

REGISTRATION_FROM_ADDRESS = 'pootle-registration@localhost'
REGISTRATION_SMTP_SERVER = 'localhost'
SUPPORT_ADDRESS = 'pootle-admin@yourdomain.org'
HOMEPAGE = 'home/'

DATABASE_ENGINE = 'sqlite3'                 # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = pootle_home(os.path.join('dbs', 'pootle.db')) # Or path to database file if using sqlite3.
DATABASE_USER = ''                          # Not used with sqlite3.
DATABASE_PASSWORD = ''                      # Not used with sqlite3.
DATABASE_HOST = ''                          # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''                          # Set to empty string for default. Not used with sqlite3.


STATS_DB_PATH = pootle_home(os.path.join('dbs', 'stats.db')) # None means the default path

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Africa/Pretoria'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = pootle_home('html')+'/'
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
    # Uncomment to use memcached for caching
    #'django.middleware.cache.UpdateCacheMiddleware', # THIS MUST BE FIRST
    'pootle_misc.middleware.baseurl.BaseUrlMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'pootle.middleware.check_cookies.CheckCookieMiddleware',
    'pootle.middleware.locale.LocaleMiddleware',
    'pootle.middleware.profile.ProfilerMiddleware',
    # Uncomment to use memcached for caching
    #'django.middleware.cache.FetchFromCacheMiddleware' # THIS MUST BE LAST
)

ROOT_URLCONF = 'pootle.urls'

TEMPLATE_CONTEXT_PROCESSORS = ("django.core.context_processors.auth",
                               "django.core.context_processors.debug",
                               "django.core.context_processors.i18n",
                               "django.core.context_processors.media",
                               "pootle_misc.context_processors.sitesettings")
TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.

    # For now we'll cheat and use a relative path, in spite of the above comment.
    pootle_home('templates'),
    pootle_home('local_apps/pootle_app/templates')
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'pootle_app',
    'pootle_misc',
    'pootle_store',
    'registration',
    'profiles',
)

AUTH_PROFILE_MODULE = "pootle_app.PootleProfile"

PREFSFILE = pootle_home('pootle.prefs')

PODIRECTORY = pootle_home('po')

# Use the commented definition to authenticate first with Mozilla's LDAP system and then to fall back
# to Django's authentication system.
#AUTHENTICATION_BACKENDS = ('auth.ldap_backend.LdapBackend', 'django.contrib.auth.backends.ModelBackend',)
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)

# LDAP Setup
# The LDAP server.  Format:  protocol://hostname:port
AUTH_LDAP_SERVER = ''
# Anonymous Credentials
AUTH_LDAP_ANON_DN = ''
AUTH_LDAP_ANON_PASS = ''
# Base DN to search
AUTH_LDAP_BASE_DN = ''
# What are we filtering on?  %s will be the username (must be in the string)
AUTH_LDAP_FILTER = ''
# This is a mapping of pootle field names to LDAP fields.  The key is pootle's name, the value should be your LDAP field name.  If you don't use the field
# or don't want to automatically retrieve these fields from LDAP comment them out.  The only required field is 'dn'.
AUTH_LDAP_FIELDS = {
        'dn':'dn',
        #'first_name':'',
        #'last_name':'',
        #'email':''
        }

LANGUAGE_NAME_COOKIE = 'pootlelang'

ENABLE_ALT_SRC = True

CAN_REGISTER = True

STORE_LRU_CACHE_SIZE = 10

ACCOUNT_ACTIVATION_DAYS = 10

# Uncomment to use memcached for caching
# CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

if DEBUG:
    logging.basicConfig(
            level = logging.DEBUG,
            format =  '%(asctime)s %(levelname)s %(message)s',
            )
else:
    # Will log only CRITICAL errors to the console
    logging.basicConfig(
            level = logging.CRITICAL,
            format =  '%(asctime)s %(levelname)s %(message)s',
            )

CONFIG_LOCATIONS = ['/etc/pootle/pootle.ini', pootle_home('pootle.ini')]

def find_config():
    # For each candidate location in CONFIG_LOCATIONS...
    for config_path in CONFIG_LOCATIONS:
        # If the location exists and is a file...
        if os.path.exists(config_path) and os.path.isfile(config_path):
            # Then we create a config parser
            config = ConfigParser()
            # Read the data at the location
            config.read(config_path)
            # And return the config
            return config
    # No valid config files were found. Bummer...
    return None

config = find_config()
if config is not None:
    vars = globals()
    """Walk through the sections in the config file and for each
    section, find the options. For each option, add a similarly
    named variable to the globals of this file.

    In other words, we don't use the sections to distinguish
    variables. But the sections in the Pootle .ini file help humans to
    understand the intention of various options."""
    for section in config.sections():
        for option in config.options(section):
            # Remember to uppercase the option name, since
            # ConfigParser conveniently lowercases our option names.
            vars[option.upper()] = config.get(section, option)


#TEST_RUNNER='pootle.pytest.run_tests'
