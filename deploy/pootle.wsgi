#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import site
import sys

ALLDIRS = [
    '%(env_path)s/lib/%(python)s/site-packages',
    '%(project_repo_path)s',
    os.path.join('%(project_repo_path)s', 'pootle', 'apps')
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


os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
