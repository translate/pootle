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

from optparse import make_option

from django.contrib.auth import get_user_model
from django.core.management.base import NoArgsCommand

from pootle_statistics.models import ScoreLog


class Command(NoArgsCommand):
    help = "Refresh score"

    shared_option_list = (
        make_option('--reset', action='store_true', dest='reset',
                    help='Reset all scores to zero'),
    )

    option_list = NoArgsCommand.option_list + shared_option_list

    def handle_noargs(self, **options):
        reset = options.get('reset', False)

        if reset:
            User = get_user_model()
            User.objects.all().update(score=0)
            ScoreLog.objects.all().delete()
