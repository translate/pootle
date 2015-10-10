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
from optparse import make_option

os.environ["DJANGO_SETTINGS_MODULE"] = "pootle.settings"

from django.contrib.auth import get_user_model

from pootle_store.models import Unit

from . import PootleCommand


User = get_user_model()


class Command(PootleCommand):
    option_list = PootleCommand.option_list + (
        make_option(
            "--from-revision",
            type=int,
            default=0,
            dest="revision",
            help="Only count contributions newer than this revision",
        ),
    )

    help = "Print a list of contributors."

    def handle_all(self, **options):
        system_user = User.objects.get_system_user()
        units = Unit.objects.exclude(submitted_by=system_user) \
                            .exclude(submitted_by=None)

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

        self.list_contributions(contribs)

    def list_contributions(self, contribs):
        out = []
        for id, count in contribs.items():
            user = User.objects.get(id=id)
            name = user.display_name
            if user.email:
                name += " <%s>" % (user.email)
            out.append("%s (%i contributions)" % (name, count))

        # Sort users alphabetically
        for line in sorted(out):
            self.stdout.write(line)
