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

# this part is only required when running from checkout instead of an install
try:
    import sys
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, ROOT_DIR) # Top level directory
    import syspath_override
except ImportError:
    # not running from checkout
    pass

# comment the above lines if running from install

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
