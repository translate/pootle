# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
# Copyright 2014-2015 Evernote Corporation
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


import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from optparse import make_option

from django.core.management.base import NoArgsCommand

from pootle.core.models import Revision


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--restore', action='store_true', default=False, dest='restore',
                    help='Restore the current revision number from the DB.'),
    )

    help = "Print the number of the current revision."

    def handle_noargs(self, **options):
        if options.get('restore'):
            from pootle_store.models import Unit
            Revision.set(Unit.max_revision())

        self.stdout.write('%s' % Revision.get())
