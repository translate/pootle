#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009, 2013 Zuza Software Foundation
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
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import PootleCommand, ModifiedSinceMixin
from pootle_store.models import TMUnit
from translate.search.lshtein import LevenshteinComparer


class Command(ModifiedSinceMixin, PootleCommand):
	option_list = PootleCommand.option_list 
	help = "Auto translate 100% matches form translation memory"

	def handle_all_stores(self, translation_project, **options):
		
		for trans_file in translation_project.get_children():
			for unit in trans_file.units:
				criteria = {
					'target_lang': unit.store.translation_project.language,
					'source_lang': unit.store.translation_project.project.source_language,
					'source_length__eq': unit.source_length,
					'target_length__gt': 1,
				}

				tmunits = TMUnit.objects.filter(**criteria)

				if len(tmunits) == 1:
					unit.target = tmunits[0].target
					unit.save()

