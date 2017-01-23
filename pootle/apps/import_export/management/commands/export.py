# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
os.environ["DJANGO_SETTINGS_MODULE"] = "pootle.settings"
from zipfile import ZipFile

from django.core.management.base import CommandError

from pootle_app.management.commands import PootleCommand
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store

from ...utils import TPTMXExporter


class Command(PootleCommand):
    help = "Export a Project, Translation Project, or path. " \
           "Multiple files will be zipped."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        group_path_or_tmx = parser.add_mutually_exclusive_group()
        group_path_or_tmx.add_argument(
            "--path",
            action="store",
            dest="pootle_path",
            help="Export a single file",
        )
        group_path_or_tmx.add_argument(
            "--tmx",
            action="store_true",
            dest="export_tmx",
            default=False,
            help="Export each translation project into a single TMX file",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            default=False,
            help="Overwrite already exported TMX files",
        )
        parser.add_argument(
            "--rotate",
            action="store_true",
            dest="rotate",
            default=False,
            help="Remove old exported TMX files",
        )

    def _create_zip(self, stores, prefix):
        with open("%s.zip" % (prefix), "wb") as f:
            with ZipFile(f, "w") as zf:
                for store in stores:
                    zf.writestr(prefix + store.pootle_path, store.serialize())

        self.stdout.write("Created %s\n" % (f.name))

    def handle_all(self, **options):
        if options['pootle_path'] is not None:
            return self.handle_path(options['pootle_path'])

        # support exporting an entire project
        if self.projects and not self.languages and not options['export_tmx']:
            for project in Project.objects.filter(code__in=self.projects):
                self.handle_project(project)
            return

        # Support exporting an entire language
        if self.languages and not self.projects and not options['export_tmx']:
            for language in Language.objects.filter(code__in=self.languages):
                self.handle_language(language)
            return

        return super(Command, self).handle_all(**options)

    def handle_translation_project(self, translation_project, **options):
        if options['export_tmx']:
            exporter = TPTMXExporter(translation_project)
            if not options['overwrite'] and exporter.file_exists():
                self.stdout.write(
                    'Translation project (%s) has not been changed.' %
                    translation_project)
                return False

            filename, removed = exporter.export(rotate=options['rotate'])
            self.stdout.write('File "%s" has been saved.' % filename)
            for filename in removed:
                self.stdout.write('File "%s" has been removed.' % filename)
        else:
            stores = translation_project.stores.live()
            prefix = "%s-%s" % (translation_project.project.code,
                                translation_project.language.code)
            self._create_zip(stores, prefix)

    def handle_project(self, project):
        stores = Store.objects.live().filter(
            translation_project__project=project)
        if not stores:
            raise CommandError("No matches for project '%s'" % (project))
        self._create_zip(stores, prefix=project.code)

    def handle_language(self, language):
        stores = Store.objects.live().filter(
            translation_project__language=language)
        self._create_zip(stores, prefix=language.code)

    def handle_path(self, path):
        stores = Store.objects.live().filter(pootle_path__startswith=path)
        if not stores:
            raise CommandError("Could not find store matching '%s'" % (path))

        if stores.count() == 1:
            store = stores.get()
            with open(os.path.basename(store.pootle_path), "wb") as f:
                f.write(store.serialize())

            self.stdout.write("Created '%s'" % (f.name))
            return

        prefix = path.strip("/").replace("/", "-")
        if not prefix:
            prefix = "export"

        self._create_zip(stores, prefix)
