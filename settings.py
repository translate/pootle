#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import logging

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

def pootle_home(filename):
    return os.path.join(ROOT_DIR, filename)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

STATS_DB_PATH = None # None means the default path

DATABASE_ENGINE = 'sqlite3'                 # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = pootle_home('../pootle.db') # Or path to database file if using sqlite3.
DATABASE_USER = ''                          # Not used with sqlite3.
DATABASE_PASSWORD = ''                      # Not used with sqlite3.
DATABASE_HOST = ''                          # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''                          # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = pootle_home('html')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

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
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'Pootle.middleware.CheckCookieMiddleware',
    'Pootle.middleware.LocaleMiddleware',
    'Pootle.middleware.RequestCacheMiddleware',
    'Pootle.middleware.ProfilerMiddleware',
    # Uncomment to use memcached for caching
    #'django.middleware.cache.FetchFromCacheMiddleware' # THIS MUST BE LAST
)

ROOT_URLCONF = 'Pootle.pootle_app.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    
    # For now we'll cheat and use a relative path, in spite of the above comment.
    pootle_home('templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'Pootle.pootle_app'
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

# Uncomment to use memcached for caching
# CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

if DEBUG:
    logging.basicConfig(
            level = logging.DEBUG,
            format =  '%(asctime)s %(levelname)s %(message)s',
            filename = pootle_home('pootle.log'),
            filemode = 'a'
            )
    logging.debug('Starting logging...')
else:
    # Will log only CRITICAL errors to the console
    logging.basicConfig(
            level = logging.CRITICAL,
            format =  '%(asctime)s %(levelname)s %(message)s',
            )
