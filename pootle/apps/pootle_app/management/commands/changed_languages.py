# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
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

from django.core.management.base import NoArgsCommand
from django.db.models import Max
from optparse import make_option
from pootle_app.management.commands import BaseRunCommand
from pootle_app.models import Revision
from pootle_store.models import Store, Unit
import sys

class Command(NoArgsCommand):
    help = "List languages that were changed since last synchronization"

    option_list = BaseRunCommand.option_list + (
        make_option('--after-revision', action='store', dest='after_revision',
                    type=int,
                    help='Show languages changed after any arbitrary revision'),
    )

    def handle_noargs(self, **options):
        last_known_revision = self.getLastKnownRevision();

        if options['after_revision'] != None:
            after_revision = int(options['after_revision'])
        else:
            after_revision = Store.objects.all().\
                aggregate(Max('last_sync_revision'))['last_sync_revision__max']\
                or -1

        print >> sys.stderr, "Will show languages changed between revisions",\
                             after_revision, "(exclusive) and",\
                             last_known_revision, "(inclusive)"

        # if the requested revision is the same or is greater than
        # the last known one, return nothing
        if after_revision >= last_known_revision:
            print >> sys.stderr, "(no known changes)"
            return

        q = Unit.objects.filter(revision__gt=after_revision)\
            .values('store__translation_project__language__code')\
            .distinct().order_by('store__translation_project__language__code')

        languages = q.values_list('store__translation_project__language__code',\
            flat=True)

        # list languages separated by comma for easy parsing
        print ','.join(languages)

    def getLastKnownRevision(self):
        try:
            return Revision.objects.values_list('counter')[0][0]
        except IndexError:
            return 0
