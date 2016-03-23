#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import os

from datetime import datetime

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from ...models import Invoice


User = get_user_model()


def is_valid_month(month_string):
    """Returns `True` if `month_string` conforms with the supported format,
    returns `False` otherwise.
    """
    try:
        datetime.strptime(month_string, '%Y-%m')
        return True
    except ValueError:
        return False


class Command(BaseCommand):
    help = "Generate invoices and send them via e-mail."

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-list',
            dest='user_list',
            help='Limit list of users for generating invoices',
            nargs='*',
            default=[],
        )

        email_group = parser.add_argument_group(
            'E-mail',
            'Controls whether invoices are sent via e-mail and how.',
        )
        email_group.add_argument(
            '--send-emails',
            action='store_true',
            dest='send_emails',
            help='Send generated invoices by email',
            default=False,
        )
        email_group.add_argument(
            '--bcc-send-to',
            dest='bcc_email_list',
            help='BCC email list',
            nargs='*',
            default=[],
        )

        debug_group = parser.add_argument_group(
            'Debugging',
            'Flags to debug invoices',
        )
        debug_group.add_argument(
            '--debug-month',
            dest='month',
            help='Month (get previous month if no data provided)',
            default=None,
        )
        debug_group.add_argument(
            '--debug-send-to',
            dest='debug_email_list',
            help='Send email to recipients (overrides existing user settings)',
            nargs='*',
            default=[],
        )

    def handle(self, **options):
        month = options['month']
        if month is not None and not is_valid_month(month):
            raise CommandError(
                '--month parameter has an invalid format: "%s", '
                'while it should be in "YYYY-MM" format'
                % month
            )

        users = settings.POOTLE_INVOICES_RECIPIENTS.items()
        if options['user_list']:
            users = filter(lambda x: x[0] in options['user_list'], users)

        # Abort if a user defined in the configuration does not exist
        user_dict = {}
        for username, user_conf in users:
            usernames = (username, ) + user_conf.get('subcontractors', ())

            for username in usernames:
                if username in user_dict:
                    continue

                try:
                    user_dict[username] = User.objects.get(username=username)
                except User.DoesNotExist:
                    raise CommandError('User %s not found.' % username)

        for username, user_conf in users:
            subcontractors = [
                user_dict[subcontractor_name]
                for subcontractor_name in user_conf.get('subcontractors', ())
            ]
            invoice = Invoice(user_dict[username], user_conf, month=month,
                              subcontractors=subcontractors,
                              add_correction=month is None)

            fullname = user_conf['name']

            self.stdout.write('Generating invoices for %s...' % fullname)
            invoice.generate()

            if not options['send_emails']:
                continue

            self.stdout.write('Sending email to %s...' % fullname)
            # FIXME: reuse connections to the mail server
            # (http://stackoverflow.com/a/10215091/783019)
            if invoice.send_by_email(override_to=options['debug_email_list'],
                                     override_bcc=options['bcc_email_list']) > 0:
                self.stdout.write('Email sent')
            else:
                self.stdout.write('ERROR: sending failed')
