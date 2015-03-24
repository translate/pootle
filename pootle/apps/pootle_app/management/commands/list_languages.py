#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from optparse import make_option

from pootle_app.management.commands import NoArgsCommandMixin


class Command(NoArgsCommandMixin):
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
        projects = options.get('projects', [])

        from pootle_translationproject.models import TranslationProject
        tps = TranslationProject.objects.distinct()
        tps = tps.exclude(language__code='templates').order_by('language__code')

        if projects:
            tps = tps.filter(project__code__in=projects)

        for lang in tps.values_list('language__code', flat=True):
            self.stdout.write(lang)
