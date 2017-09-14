# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import traceback

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.db import transaction
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.core.management import CommandError
from django.core.validators import validate_email

from pootle.core.delegate import formats
from pootle_fs.delegate import fs_plugins
from pootle_fs.presets import FS_PRESETS
from pootle_language.models import Language
from pootle_project.models import Project, PROJECT_CHECKERS


class Command(BaseCommand):
    help = "Creates a new project from command line."

    def add_arguments(self, parser):
        format_names = formats.get().keys()
        fs_plugins_names = fs_plugins.gather().keys()

        parser.add_argument(
            'code',
            action='store',
            help='Project code',
        )
        parser.add_argument(
            "--name",
            action="store",
            dest="name",
            help="Project name",
        )
        parser.add_argument(
            "--filetype",
            action="append",
            dest="filetypes",
            choices=format_names,
            default=[],
            help="File types: {0}. Default: po".format(
                 " | ".join(format_names)),
        )
        mapping_group = parser.add_mutually_exclusive_group(required=True)
        mapping_group.add_argument(
            "--preset-mapping",
            action="store",
            dest="preset_mapping",
            choices=FS_PRESETS.keys(),
            help="Filesystem layout preset: {0}".format(
                 " | ".join(FS_PRESETS.keys())),
        )
        mapping_group.add_argument(
            "--mapping",
            action="store",
            dest="mapping",
            help="Custom filesystem layout",
        )
        parser.add_argument(
            "--fs-type",
            action="store",
            dest="fs_type",
            default="localfs",
            choices=fs_plugins_names,
            help="Filesystem type: {0}".format(" | ".join(fs_plugins_names)),
        )
        parser.add_argument(
            "--fs-url",
            action="store",
            dest="fs_url",
            default="",
            help="Filesystem path or URL.",
        )
        parser.add_argument(
            "--source-language",
            action="store",
            dest="sourcelang",
            default="en",
            help=("Source language. Examples: [en | es | fr | ...]."
                  "Default: %(default)s"),
        )
        parser.add_argument(
            "--report-email",
            action="store",
            default="",
            dest="contact",
            help="Contact email for reports. Example: admin@mail.com.",
        )
        parser.add_argument(
            "--disabled",
            action="store_true",
            dest="disabled",
            help="Does the project start disabled?",
        )
        parser.add_argument(
            "--checkstyle",
            action="store",
            dest="checkstyle",
            choices=PROJECT_CHECKERS.keys(),
            default="standard",
            help="Quality check styles. Example: {0}. Default: %(default)s"
                 .format(" | ".join(PROJECT_CHECKERS.keys())),
        )

    @transaction.atomic
    def handle(self, **options):
        """Imitates the behaviour of the admin interface
        for creating a project from command line.
        """
        self.check_project_options(**options)
        self.set_project_config(
            self.create_project(**options), **options)

    def check_project_options(self, **options):
        if options["contact"]:
            try:
                validate_email(options["contact"])
            except ValidationError as e:
                if options["traceback"]:
                    traceback.print_exc()
                raise CommandError(e)
        if options["fs_type"] != "localfs" and options["fs_url"] == "":
            raise CommandError("Parameter --fs-url is mandatory "
                               "when --fs-type is not `localfs`")

    def create_project(self, **options):
        try:
            return Project.objects.create(
                code=options["code"],
                fullname=options["name"] or options["code"].capitalize(),
                checkstyle=options["checkstyle"],
                source_language=self.get_source_language(**options),
                filetypes=options["filetypes"] or ["po"],
                report_email=options["contact"],
                disabled=options["disabled"])
        except ValidationError as e:
            if options["traceback"]:
                traceback.print_exc()
            raise CommandError(e)

    def get_source_language(self, **options):
        try:
            return Language.objects.get(code=options["sourcelang"])
        except Language.DoesNotExist:
            raise CommandError("Source language %s does not exist"
                               % options["sourcelang"])

    def set_project_config(self, project, **options):
        mapping = (
            dict(default=FS_PRESETS[options["preset_mapping"]][0])
            if options["preset_mapping"]
            else dict(default=options["mapping"]))
        try:
            project.config["pootle_fs.translation_mapping"] = mapping
            project.config["pootle_fs.fs_type"] = options["fs_type"]
            if options["fs_url"]:
                project.config["pootle_fs.fs_url"] = options["fs_url"]
        except ValidationError as e:
            if options["traceback"]:
                traceback.print_exc()
            raise CommandError(e)
