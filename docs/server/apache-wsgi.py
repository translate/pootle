#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import site
import sys


# You probably will need to change these paths to match your deployment,
# most likely because of the Python version you are using.
ALLDIRS = [
    '/var/www/pootle/env/lib/python2.7/site-packages',
    '/var/www/pootle/env/lib/python2.7/site-packages/pootle/apps',
]

# Remember original sys.path.
prev_sys_path = list(sys.path)

# Add each new site-packages directory.
for directory in ALLDIRS:
    site.addsitedir(directory)

# Reorder sys.path so new directories at the front.
new_sys_path = []

for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)

sys.path[:0] = new_sys_path

# Set the Pootle settings module as DJANGO_SETTINGS_MODULE.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

# Set the WSGI application.
def application(environ, start_response):
    """Wrapper for Django's WSGIHandler().

    This allows to get values specified by SetEnv in the Apache
    configuration or interpose other changes to that environment, like
    installing middleware.
    """
    try:
        os.environ['POOTLE_SETTINGS'] = environ['POOTLE_SETTINGS']
    except KeyError:
        pass

    from django.core.wsgi import get_wsgi_application
    _wsgi_application = get_wsgi_application()
    return _wsgi_application(environ, start_response)
