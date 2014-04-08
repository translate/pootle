#!/usr/bin/env python
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
import json

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from optparse import make_option

from pootle_app.management.commands import PootleCommand
from pootle_app.models import Directory
from pootle_misc.util import PootleJSONEncoder

DUMPED = {
    'TranslationProject': ('pootle_path', 'real_path', 'disabled'),
    'Store': ('file', 'translation_project', 'pootle_path', 'name', 'state'),
    'Directory': ('name', 'parent', 'pootle_path'),
    'Unit': ('source', 'target', 'source_wordcount', 'target_wordcount',
             'developer_comment', 'translator_comment', 'locations',
             'isobsolete', 'isfuzzy', 'istranslated'),
    'Suggestion': ('target_f', 'user_id'),
    'Language': ('code', 'fullname', 'pootle_path'),
    'Project': ('code', 'fullname', 'checkstyle', 'localfiletype',
                'treestyle', 'source_language', 'ignoredfiles',
                'screenshot_search_prefix', 'disabled')
}


class Command(PootleCommand):
    help = "Dump data."

    shared_option_list = (
        make_option('--stats', action='store_true', dest='stats',
                    help='Dump stats'),
        make_option('--data', action='store_true', dest='data',
                    help='Data all data'),
        make_option('--stop-level', action='store', dest='stop_level',
                    default=-1),
        )
    option_list = PootleCommand.option_list + shared_option_list

    def handle_all(self, **options):
        stats = options.get('stats', False)
        data = options.get('data', False)
        stop_level = int(options.get('stop_level', -1))
        if stats:
            self.dump_stats(stop_level=stop_level)
        if data:
            self.dump_all(stop_level=stop_level)

    def handle_translation_project(self, tp, **options):
        stats = options.get('stats', False)
        data = options.get('data', False)
        stop_level = int(options.get('stop_level', -1))
        if stats:
            res = {}
            self._dump_stats(tp.directory, res, stop_level=stop_level)

            stats_dump = json.dumps(res, indent=4, cls=PootleJSONEncoder)
            self.stdout.write(stats_dump)
        if data:
            self._dump_item(tp.directory, 0, stop_level=stop_level)

    def dump_stats(self, stop_level):
        root = Directory.objects.root
        projects = Directory.objects.projects
        res = {}
        self._dump_stats(root, res, stop_level=stop_level)
        # stop on translation project level -> stop_level = 2
        self._dump_stats(projects, res, stop_level=2)

        stats_dump = json.dumps(res, indent=4, cls=PootleJSONEncoder)
        self.stdout.write(stats_dump)


    def _dump_stats(self, item, res, stop_level):
        res[item.code] = {}
        item.initialize_children()

        if stop_level != 0 and item.children:
            res[item.code]['children'] = {}
            if stop_level > 0:
                stop_level = stop_level - 1
            for child in item.children:
                self._dump_stats(child, res[item.code]['children'],
                                 stop_level=stop_level)

        res[item.code].update(item.get_stats(include_children=False))

    def dump_all(self, stop_level):
        root = Directory.objects.root
        self._dump_item(root, 0, stop_level=stop_level)

    def _dump_item(self, item, level, stop_level):
        self.stdout.write(self.dumped(item))
        if item.is_dir:
            if item.is_project():
                self.stdout.write(self.dumped(item.project))
            elif item.is_language():
                self.stdout.write(self.dumped(item.language))
            elif item.is_translationproject():
                try:
                    self.stdout.write(self.dumped(item.translationproject))
                except:
                    pass
        else:
            # item should be a Store
            for unit in item.units:
                self.stdout.write(self.dumped(unit))
                for sg in unit.get_suggestions():
                    self.stdout.write(self.dumped(sg))

        if stop_level != level:
            item.initialize_children()
            if item.children:
                for child in item.children:
                    self._dump_item(child, level + 1, stop_level=stop_level)

    def dumped(self, item):
        def get_param(param):
            p = getattr(item, param)
            res = p() if callable(p) else p
            res = u"%s" % res
            res = res.replace('\n', '\\n')
            return (param, res)

        return u"%d:%s\t%s" % \
            (
                item.id,
                item._meta.object_name,
                "\t".join(
                    u"%s=%s" % (k, v)
                    for k, v in map(get_param, DUMPED[item._meta.object_name])
                )
            )
