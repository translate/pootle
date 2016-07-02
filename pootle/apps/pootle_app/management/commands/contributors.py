# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from argparse import ArgumentTypeError
from collections import Counter
from dateutil.parser import parse as parse_datetime

os.environ["DJANGO_SETTINGS_MODULE"] = "pootle.settings"

from django.contrib.auth import get_user_model

from pootle.core.utils.timezone import make_aware
from pootle_store.models import Unit

from . import PootleCommand


User = get_user_model()


def get_aware_datetime(dt_string):
    """Return an aware datetime parsed from a datetime or date string.

    Datetime or date string can be any format parsable by dateutil.parser.parse
    """
    if not dt_string:
        return None
    try:
        return make_aware(parse_datetime(dt_string))
    except ValueError:
        raise ArgumentTypeError('The provided datetime/date string is not '
                                'valid: "%s"' % dt_string)


class Command(PootleCommand):
    help = "Print a list of contributors."
    requires_system_checks = False

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--since",
            type=get_aware_datetime,
            action="store",
            dest="since",
            help=('ISO 8601 format: 2016-01-24T23:15:22+0000 or '
                  '"2016-01-24 23:15:22 +0000" or "2016-01-24"'),
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

    def _get_revision_from_since(self, since):
        from pootle_statistics.models import Submission

        submissions_qs = Submission.objects.filter(creation_time__lt=since)

        if self.projects:
            submissions_qs = submissions_qs.filter(
                translation_project__project__code__in=self.projects,
            )

        if self.languages:
            submissions_qs = submissions_qs.filter(
                translation_project__language__code__in=self.languages,
            )

        submission = submissions_qs.last()

        if submission is None:
            return 0

        return submission.unit.revision

    def handle_all(self, **options):
        system_user = User.objects.get_system_user()
        units = Unit.objects.exclude(submitted_by=system_user) \
                            .exclude(submitted_by=None)

        if options["only_emails"]:
            nobody_user = User.objects.get_nobody_user()
            units = units.exclude(submitted_by=nobody_user)

        if options["since"]:
            units = units.filter(
                revision__gte=self._get_revision_from_since(options["since"]),
            )

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
            if only_emails:
                name = name.replace(",", "")
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
