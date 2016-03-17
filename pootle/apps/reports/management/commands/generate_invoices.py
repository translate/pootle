#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import codecs
import logging
import os
import re
import urllib2

from datetime import timedelta
from subprocess import call

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.core.urlresolvers import set_script_prefix
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_unicode
from django.utils.html import strip_tags

from ...models import PaidTaskTypes, PaidTask
from ...views import (get_date_interval, get_grouped_word_stats, get_rates,
                      get_tasks, get_scores, SCORE_TRANSLATION_PROJECT)


logger = logging.getLogger(__name__)


def get_previous_month():
    now = timezone.now()
    previous_month = now.replace(day=1) - timedelta(days=1)

    return previous_month.strftime('%Y-%m')


class Command(BaseCommand):
    help = "Generate invoices and send them via e-mail."

    change_rates = {}

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-list',
            action='append',
            dest='user_list',
            help='Limit list of users for generating invoices',
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
            action='append',
            dest='bcc_email_list',
            help='BCC email list',
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
            action='append',
            dest='debug_email_list',
            help='Send email to recipients (overrides existing user settings)',
            default=[],
        )

    def get_change_rate(self, currency, date):
        if currency not in self.change_rates:
            url = 'http://www.x-rates.com/average/?from=%s&to=USD&year=%s' % \
                  (currency, date.year)
            self.stdout.write(
                'Loading USD/%s exchange rate from external service'
                % currency
            )

            try:
                html = urllib2.urlopen(url).read()
                regex = re.compile(r"'monthlyCanvas',\[(.*?)\]", re.DOTALL)
                match = regex.search(html)
                if match is None:
                    raise

                monthly_avg = re.split(",", match.group(1))
                self.change_rates[currency] = round(
                    float(monthly_avg[date.month - 1]),
                    3,
                )

            except Exception:
                # set change rate to zero to invalidate summary
                # if we couldn't get a proper value
                self.stdout.write(
                    'ERROR: Failed to get %s/USD change rate.'
                    % currency
                )
                exit(1)

        return self.change_rates[currency]

    def html2pdf(self, html_filename, pdf_filename):
        if hasattr(settings, 'POOTLE_INVOICES_PHANTOMJS_BIN'):
            html2pdf_js = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                       '../../', 'html2pdf.js')
            self.stdout.write("Saving PDF to '%s'" % pdf_filename)
            result = call([settings.POOTLE_INVOICES_PHANTOMJS_BIN,
                           html2pdf_js, html_filename, pdf_filename])
            if result:
                self.stdout.write('Script returned result: %s' % result)

    def send_invoice(self, subject, to, cc, bcc, html, pdf_file):
        # set non-empty body according
        # http://stackoverflow.com/questions/14580176/confusion-with-sending-email-in-django
        mail = EmailMultiAlternatives(subject=subject, body=strip_tags(html),
                                      to=to, cc=cc, bcc=bcc)
        mail.attach_alternative(html, 'text/html')
        if pdf_file is not None:
            mail.attach_file(pdf_file, 'application/pdf')
        self.stdout.write("Sending email to %s" % to)
        if mail.send() > 0:
            self.stdout.write("Email sent")
        else:
            self.stdout.write("ERROR: sending failed")

    def handle(self, **options):
        # The script prefix needs to be set here because the generated URLs need
        # to be aware of that and they are cached. Ideally Django should take
        # care of setting this up, but it's only available starting from
        # Django 1.10: https://code.djangoproject.com/ticket/16734
        script_name = (u'/' if settings.FORCE_SCRIPT_NAME is None
                       else force_unicode(settings.FORCE_SCRIPT_NAME))
        set_script_prefix(script_name)

        if not hasattr(settings, 'POOTLE_INVOICES_PHANTOMJS_BIN'):
            self.stdout.write(
                'NOTICE: settings.POOTLE_INVOICES_PHANTOMJS_BIN not defined; '
                'PDFs will not be generated'
            )

        month = options.get('month', None)
        add_correction = False
        if month is None:
            month = get_previous_month()
            add_correction = True

        send_emails = options.get('send_emails', False)
        debug_email_list = []
        for item in options.get('debug_email_list', []):
            debug_email_list += item.split(',')
        bcc_email_list = []
        for item in options.get('bcc_email_list', []):
            bcc_email_list += item.split(',')
        user_list = []
        for item in options.get('user_list', []):
            user_list += item.split(',')

        now = timezone.now()
        try:
            [start, end] = get_date_interval(month)
        except ValueError:
            self.stdout.write(
                '--month parameter has an invalid format: "%s", '
                'while it should be in "YYYY-MM" format'
                % month
            )
            exit(1)

        date = end if now > end else now
        month_dir = os.path.join(settings.POOTLE_INVOICES_DIRECTORY, month)
        if not os.path.exists(month_dir):
            os.makedirs(month_dir)

        subcontractors = ()
        for username, user_conf in settings.POOTLE_INVOICES_RECIPIENTS.items():
            if 'subcontractors' in user_conf:
                subcontractors += user_conf['subcontractors']

        users = settings.POOTLE_INVOICES_RECIPIENTS.items()
        if user_list:
            users = filter(lambda x: x[0] in user_list, users)

        user_dict = {}

        for username, user_conf in users:
            usernames = (username, )
            main_username = username
            if 'subcontractors' in user_conf:
                usernames += user_conf['subcontractors']

            for username in usernames:
                if username in user_dict:
                    continue

                try:
                    User = get_user_model()
                    user_dict[username] = User.objects.get(username=username)
                except User.DoesNotExist:
                    self.stdout.write('ERROR: User %s not found.' % username)
                    exit(1)

            user = user_dict[main_username]
            if user.currency != 'USD':
                self.get_change_rate(user.currency, start)

        for username, user_conf in users:
            ctx = {
                'translated_words': 0,
                'reviewed_words': 0,
                'hours': 0,
                'correction': 0,
            }

            usernames = (username, )
            main_username = username
            if 'subcontractors' in user_conf:
                usernames += user_conf['subcontractors']

            for username in usernames:
                self.stdout.write('Getting data for %s' % username)
                user = user_dict[username]
                if main_username == username:
                    main_user = user
                    rate, review_rate, hourly_rate = \
                        get_rates(main_user, start, end)

                scores = get_scores(user, start, end)
                scores = scores.order_by(SCORE_TRANSLATION_PROJECT)
                for row in get_grouped_word_stats(scores):
                    ctx['translated_words'] += row['translated']
                    ctx['reviewed_words'] += row['reviewed']

                tasks = get_tasks(user, start, end)
                for task in tasks:
                    if task.task_type == PaidTaskTypes.TRANSLATION:
                        ctx['translated_words'] += task.amount
                    elif task.task_type == PaidTaskTypes.REVIEW:
                        ctx['reviewed_words'] += task.amount
                    elif task.task_type == PaidTaskTypes.HOURLY_WORK:
                        ctx['hours'] += task.amount
                    elif task.task_type == PaidTaskTypes.CORRECTION:
                        ctx['correction'] += task.amount

            ctx['translated_words'] = int(round(ctx['translated_words']))
            ctx['reviewed_words'] = int(round(ctx['reviewed_words']))

            ctx['translation_amount'] = round(ctx['translated_words'] * rate, 2)
            ctx['review_amount'] = round(ctx['reviewed_words'] * review_rate, 2)
            ctx['hours_amount'] = round(ctx['hours'] * hourly_rate, 2)

            ctx['total'] = ctx['translation_amount'] + ctx['review_amount'] + \
                ctx['hours_amount'] + ctx['correction']

            ctx['minimal_payment'] = user_conf.get('minimal_payment', 0)
            ctx['correction_added'] = False

            if add_correction:
                tz = timezone.get_default_timezone()
                if ctx['total'] > 0 and ctx['total'] < ctx['minimal_payment']:
                    first_moment = now.replace(day=1, hour=0, minute=0,
                                               second=0, tzinfo=tz)
                    PaidTask.objects.create(
                        task_type=PaidTaskTypes.CORRECTION,
                        amount=(-1) * ctx['total'],
                        rate=1,
                        datetime=end,
                        description='Carryover to the next month',
                        user=user,
                    )
                    PaidTask.objects.create(
                        task_type=PaidTaskTypes.CORRECTION,
                        amount=ctx['total'],
                        rate=1,
                        datetime=first_moment,
                        description='Carryover from the previous month',
                        user=user,
                    )
                    ctx['correction_added'] = True
                    ctx['balance'] = ctx['total']
                    ctx['total'] = 0

            ctx['extra_amount'] = 0
            if 'extra_add' in user_conf and ctx['total'] > 0:
                ctx['extra_amount'] += user_conf['extra_add']
            if 'extra_multiply' in user_conf:
                ctx['extra_amount'] += \
                    ctx['total'] * (user_conf['extra_multiply'] - 1)

            ctx['user'] = main_user
            ctx['id'] = user_conf['invoice_prefix'] + month
            ctx['date'] = date
            ctx['month'] = start
            ctx['rate'] = rate
            ctx['review_rate'] = review_rate
            ctx['hourly_rate'] = hourly_rate
            ctx['debug_emails'] = debug_email_list

            # add extra_amount after marketing / product translations relation
            # was calculated
            ctx['total'] += ctx['extra_amount']

            user_conf['wire_info'] = user_conf['wire_info'].lstrip()
            user_conf['paid_by'] = user_conf['paid_by'].lstrip()
            ctx.update(user_conf)

            name = 'Invoice - %s - %s' % (ctx['name'], ctx['id'])

            filename = os.path.join(month_dir, name)

            html_filename = filename + '.html'
            pdf_filename = filename + '.pdf'

            self.stdout.write("Saving HTML to '%s'" % html_filename)
            html = render_to_string('invoices/invoice.html', ctx)
            codecs.open(html_filename, 'w', 'utf-8').write(html)
            self.html2pdf(html_filename, pdf_filename)

            if send_emails:
                if 'accounting-email' not in user_conf:
                    logger.warning(
                        '`accounting_email` not found in configuration for '
                        'user %s. Sending email will be skipped for this user.',
                        username,
                    )
                    continue

                ctx['bcc_email_list'] = bcc_email_list
                ctx['accounting'] = True
                ctx['to_email_list'] = user_conf['accounting-email'].split(',')
                ctx['cc_email_list'] = None
                if 'accounting-email-cc' in user_conf:
                    ctx['cc_email_list'] = (
                        user_conf['accounting-email-cc'].split(',')
                    )

                if ctx['total'] > 0:
                    subject = (
                        u'For payment: Invoice %s, %s'
                        % (ctx['id'], ctx['name'])
                    )
                    to = debug_email_list or ctx['to_email_list']
                    cc = ctx['cc_email_list']
                    if debug_email_list:
                        cc = None
                    html = render_to_string('invoices/invoice_message.html', ctx)
                    self.send_invoice(subject, to, cc, bcc_email_list,
                                      html, pdf_filename)

                ctx['accounting'] = False
                ctx['to_email_list'] = user_conf['email'].split(',')
                ctx['cc_email_list'] = None

                if ctx['total'] > 0:
                    html = render_to_string('invoices/invoice_message.html', ctx)
                    subject = (
                        u'Sent for payment: Invoice %s, %s'
                        % (ctx['id'], ctx['name'])
                    )
                else:
                    subject = (
                        u'Notice: No payment will be sent this month to %s'
                        % ctx['name']
                    )
                    html = render_to_string('invoices/no_invoice_message.html', ctx)
                    pdf_filename = None
                    if ctx['correction_added']:
                        subject += u"; unpaid balance carried over to next month"

                to = debug_email_list or ctx['to_email_list']
                self.send_invoice(subject, to, None,
                                  bcc_email_list, html, pdf_filename)
