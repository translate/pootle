# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from argparse import ArgumentTypeError
from dateutil.parser import parse as parse_datetime
from email.utils import formataddr

os.environ["DJANGO_SETTINGS_MODULE"] = "pootle.settings"

from pootle.core.delegate import contributors
from pootle.core.utils.timezone import make_aware

from . import PootleCommand


def get_aware_datetime(dt_string, tz=None):
    """Return an aware datetime parsed from a datetime or date string.

    :param dt_string: datetime or date string can be any format parsable by
        dateutil.parser.parse.
    :param tz: timezone in which `dt_string` should be
        considered.
    """
    if not dt_string:
        return None
    try:
        return make_aware(parse_datetime(dt_string), tz=tz)
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
            "--until",
            type=get_aware_datetime,
            action="store",
            dest="until",
            help=('ISO 8601 format: 2016-01-24T23:15:22+0000 or '
                  '"2016-01-24 23:15:22 +0000" or "2016-01-24"'),
        )
        parser.add_argument(
            "--sort-by",
            default="username",
            choices=["username", "contributions"],
            dest="sort_by",
            help="Sort by specified item. Accepts: %(choices)s. "
                 "Default: %(default)s",
        )
        anon_or_mailmerge = parser.add_mutually_exclusive_group(required=False)
        anon_or_mailmerge.add_argument(
            "--include-anonymous",
            action="store_true",
            dest="include_anon",
            help="Include anonymous contributions.",
        )
        anon_or_mailmerge.add_argument(
            "--mailmerge",
            action="store_true",
            dest="mailmerge",
            help="Output only names and email addresses. Contribution counts "
                 "are excluded.",
        )

    @property
    def contributors(self):
        return contributors.get()

    def contrib_kwargs(self, **options):
        kwargs = {
            k: v
            for k, v
            in options.items()
            if k in ["projects", "languages", "include_anon",
                     "since", "until", "sort_by"]}
        kwargs["project_codes"] = kwargs.pop("projects", None)
        kwargs["language_codes"] = kwargs.pop("languages", None)
        return kwargs

    def handle(self, **options):
        contributors = self.contributors(**self.contrib_kwargs(**options))
        for username, user in contributors.items():
            name = user["full_name"].strip() or username

            if options["mailmerge"]:
                email = user["email"].strip()
                if email:
                    self.stdout.write(formataddr((name, email)))
            else:
                self.stdout.write("%s (%s contributions)" %
                                  (name, user["contributions"]))
