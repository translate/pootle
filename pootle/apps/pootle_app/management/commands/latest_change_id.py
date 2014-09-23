# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
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

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import NoArgsCommand
from pootle_statistics.models import Submission


class Command(NoArgsCommand):

    help = "Print the ID of the latest change made."

    def handle_noargs(self, **options):
        try:
            changeid = Submission.objects.values_list("id", flat=True) \
                       .select_related("").latest()
        except Submission.DoesNotExist:
            # if there is no latest id, treat it as id 0
            changeid = 0
        self.stdout.write("%i\n" % (changeid))
