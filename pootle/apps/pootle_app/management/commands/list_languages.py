#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import (NoArgsCommandMixin,
                                            ModifiedSinceMixin)


class Command(ModifiedSinceMixin, NoArgsCommandMixin):
    option_list = NoArgsCommandMixin.option_list + (
            make_option('--project', action='append', dest='projects',
                        help='Limit to PROJECTS'),
    )
    help = "List language codes."

    def handle_noargs(self, **options):
        super(Command, self).handle_noargs(**options)
        self.list_languages(**options)

    def list_languages(self, **options):
        """List all languages on the server or the given projects."""
        change_id = options.get('modified_since', 0)
        projects = options.get('projects', [])

        from pootle_translationproject.models import TranslationProject
        tps = TranslationProject.objects.distinct()
        tps = tps.exclude(language__code='templates').order_by('language__code')

        if change_id:
            tps = tps.filter(submission__id__gt=change_id)

        if projects:
            tps = tps.filter(project__code__in=projects)

        for lang in tps.values_list('language__code', flat=True):
            self.stdout.write(lang)
