#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from collections import Counter

os.environ["DJANGO_SETTINGS_MODULE"] = "pootle.settings"

from django.contrib.auth import get_user_model

from pootle_store.models import Unit

from . import PootleCommand


User = get_user_model()


class Command(PootleCommand):
    help = "Print a list of contributors."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--from-revision",
            type=int,
            default=0,
            dest="revision",
            help="Only count contributions newer than this revision",
        )
        parser.add_argument(
            "--sort-by",
            default="name",
            choices=["name", "contributions"],
            dest="sort_by",
            help="Sort by specified item. Accepts: %(choices)s. "
                 "Default: %(default)s",
        )
        parser.add_argument(
            "--only-emails",
            action="store_true",
            dest="only_emails",
            help="Output only names and email addresses. Contribution counts "
                 "are excluded.",
        )

    def handle_all(self, **options):
        system_user = User.objects.get_system_user()
        units = Unit.objects.exclude(submitted_by=system_user) \
                            .exclude(submitted_by=None)

        if options["only_emails"]:
            nobody_user = User.objects.get_nobody_user()
            units = units.exclude(submitted_by=nobody_user)

        if options["revision"]:
            units = units.filter(revision__gte=options["revision"])

        if self.projects:
            units = units.filter(
                store__translation_project__project__code__in=self.projects,
            )

        if self.languages:
            units = units.filter(
                store__translation_project__language__code__in=self.languages,
            )

        contribs = Counter()
        for v in units.values("submitted_by"):
            contribs.update((v["submitted_by"], ))

        self.list_contributions(contribs, options["sort_by"],
                                options["only_emails"])

    def list_contributions(self, contribs, sort_by, only_emails):
        if sort_by == "name":
            contributions = contribs.items()
        else:
            contributions = contribs.most_common()

        out = []
        for id, count in contributions:
            user = User.objects.get(id=id)
            name = user.display_name
            if user.email:
                name += " <%s>" % (user.email)
            elif only_emails:
                continue
            if not only_emails:
                name = "%s (%i contributions)" % (name, count)
            out.append(name)

        if sort_by == "name":
            # Sort users alphabetically
            out = sorted(out)

        for line in out:
            self.stdout.write(line)
