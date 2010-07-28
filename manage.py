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

import syspath_override

from django.core.management import execute_manager
try:
    from pootle import settings
except ImportError:
    import sys
    sys.stderr.write("""Error: Can't find the file 'settings.py' in the directory containing %r.
It appears you've customized things.

You'll have to run django-admin.py, passing it your settings module.
(If the file settings.py does indeed exist, it's causing an ImportError somehow.)""" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
