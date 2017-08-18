# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import CommandError

from pootle_app.management.commands import PootleCommand
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


DUMPED = {
    'TranslationProject': ('pootle_path', 'disabled'),
    'Store': ('translation_project', 'pootle_path', 'name', 'state'),
    'Directory': ('name', 'parent', 'pootle_path'),
    'Unit': ('source', 'target', 'target_wordcount',
             'developer_comment', 'translator_comment', 'locations',
             'isobsolete', 'isfuzzy', 'istranslated'),
    'UnitSource': ('source_wordcount', ),
    'Suggestion': ('target_f', 'user_id'),
    'Language': ('code', 'fullname', 'pootle_path'),
    'Project': ('code', 'fullname', 'checkstyle',
                'source_language', 'ignoredfiles',
                'screenshot_search_prefix', 'disabled')
}


class Command(PootleCommand):
    help = "Dump data."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--stats',
            action='store_true',
            dest='stats',
            default=False,
            help='Dump stats',
        )
        parser.add_argument(
            '--data',
            action='store_true',
            dest='data',
            default=False,
            help='Data all data',
        )
        parser.add_argument(
            '--stop-level',
            action='store',
            dest='stop_level',
            default=-1,
            type=int,
            help="Depth of data to retrieve",
        )

    def handle_all(self, **options):
        if not self.projects and not self.languages:

            if options['stats']:
                self.dump_stats(stop_level=options['stop_level'])
                return
            if options['data']:
                self.dump_all(stop_level=options['stop_level'])
                return

            raise CommandError("Set --data or --stats option.")
        else:
            super(Command, self).handle_all(**options)

    def handle_translation_project(self, tp, **options):
        if options['stats']:
            res = {}
            self._dump_stats(tp.directory, res,
                             stop_level=options['stop_level'])
            return

        if options['data']:
            self._dump_item(tp.directory, 0, stop_level=options['stop_level'])
            return

        raise CommandError("Set --data or --stats option.")

    def dump_stats(self, stop_level):
        res = {}
        for prj in Project.objects.all():
            self._dump_stats(prj, res, stop_level=stop_level)

    def _dump_stats(self, item, res, stop_level):
        key = item.pootle_path
        item.initialize_children()

        if stop_level != 0 and item.children:
            if stop_level > 0:
                stop_level = stop_level - 1
            for child in item.children:
                self._dump_stats(child, res,
                                 stop_level=stop_level)

        res[key] = (item.data_tool.get_stats(include_children=False))

        if res[key]['last_submission']:
            if 'id' in res[key]['last_submission']:
                last_submission_id = res[key]['last_submission']['id']
            else:
                last_submission_id = None
        else:
            last_submission_id = None

        if res[key]['last_created_unit']:
            if 'id' in res[key]['last_created_unit']:
                last_updated_id = res[key]['last_created_unit']['id']
            else:
                last_updated_id = None
        else:
            last_updated_id = None

        out = u"%s  %s,%s,%s,%s,%s,%s,%s" % \
              (key, res[key]['total'], res[key]['translated'],
               res[key]['fuzzy'], res[key]['suggestions'],
               res[key]['critical'],
               last_submission_id, last_updated_id)

        self.stdout.write(out)

    def dump_all(self, stop_level):
        root = Directory.objects.root
        self._dump_item(root, 0, stop_level=stop_level)

    def _dump_item(self, item, level, stop_level):
        self.stdout.write(self.dumped(item))
        if isinstance(item, Directory):
            pass
        elif isinstance(item, Language):
            self.stdout.write(self.dumped(item.language))
        elif isinstance(item, TranslationProject):
            try:
                self.stdout.write(self.dumped(item.translationproject))
            except:
                pass
        elif isinstance(item, Project):
            pass
            # self.stdout.write(self.dumped(item))
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
