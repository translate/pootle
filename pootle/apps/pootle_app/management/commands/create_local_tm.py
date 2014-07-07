#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

import os
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import BaseCommand
from django.db import transaction

from pootle_store.models import TMUnit, Unit
from pootle_store.util import TRANSLATED


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--drop-local-tm", dest="drop_local_tm",
                    action="store_true", help="Drop any existing local TM"),
    )
    help = ("Recreate the local translation memory.")

    def handle(self, *args, **options):
        """Recreate the local TM using translations from existing projects.

        Iterates over all the translation units and creates the corresponding
        local TM units.
        """
        if options["drop_local_tm"]:
            self.stdout.write('About to drop existing previous local TM')
            TMUnit.objects.all().delete()
            self.stdout.write('Successfully dropped existing local TM')

        self.stdout.write('About to create local TM using existing translations')
        with transaction.commit_on_success():
            for unit in Unit.objects.filter(state__gte=TRANSLATED).iterator():
                tmunit = TMUnit().create(unit)
                tmunit.save()

        self.stdout.write('Successfully created local TM from existing translations')
