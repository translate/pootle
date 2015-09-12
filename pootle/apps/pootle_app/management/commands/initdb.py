#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
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

import logging
import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    help = 'Populates the database with initial values: users, projects, ...'

    def handle_noargs(self, **options):
        logging.warning("\n\n\n    Warning: Pootle 2.6.1 is an interim "
                        "release (a migration step to Pootle"
                        "\n             2.7.0), so it can't be installed.\n\n"
                        "No change has been done.\n\n")
