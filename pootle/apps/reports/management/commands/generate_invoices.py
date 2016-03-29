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

from datetime import datetime, timedelta
from subprocess import call

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from pootle_misc.util import get_date_interval
from pootle_statistics.models import ScoreLog

from ...models import PaidTaskTypes, PaidTask
from ...views import get_grouped_word_stats, SCORE_TRANSLATION_PROJECT


logger = logging.getLogger(__name__)

User = get_user_model()


def get_previous_month():
    now = timezone.now()
    previous_month = now.replace(day=1) - timedelta(days=1)

    return previous_month.strftime('%Y-%m')


def is_valid_month(month_string):
    """Returns `True` if `month_string` conforms with the supported format,
    returns `False` otherwise.
    """
    try:
        datetime.strptime(month_string, '%Y-%m')
        return True
    except ValueError:
        return False


def get_rates(user, start, end):
    """Get user rates that were set for the user during a period
    from start to end. Raise an exception if the user has multiple rates
    during the period.

    :param user: get rates for this User object.
    :param start: datetime
    :param end: datetime
    :return: a tuple ``(rate, review_rate, hourly_rate)`` where ``rate`` is the
        translation rate, and ``review_rate`` is the review rate, and
        ``hourly_rate`` is the rate for hourly work that can be added as
        PaidTask.
    """
    scores = ScoreLog.objects.for_user_in_range(user, start, end)
    rate, review_rate, hourly_rate = 0, 0, 0
    rates = scores.values('rate', 'review_rate').distinct()
    if len(rates) > 1:
        raise Exception("Multiple user [%s] rate values." % user.username)
    elif len(rates) == 1:
        rate = rates[0]['rate']
        review_rate = rates[0]['review_rate']

    tasks = PaidTask.objects.for_user_in_range(user, start, end)
    task_rates = tasks.values('task_type', 'rate').distinct()
    for task_rate in task_rates:
        if (task_rate['task_type'] == PaidTaskTypes.TRANSLATION and
            rate > 0 and
            task_rate['rate'] != rate):
            raise Exception("Multiple user [%s] rate values." % user.username)
        if (task_rate['task_type'] == PaidTaskTypes.REVIEW and
            review_rate > 0 and
            task_rate['rate'] != review_rate):
            raise Exception("Multiple user [%s] rate values." % user.username)
        if task_rate['task_type'] == PaidTaskTypes.HOURLY_WORK:
            if hourly_rate > 0 and task_rate['rate'] != hourly_rate:
                raise Exception("Multiple user [%s] rate values." %
                                user.username)
            hourly_rate = task_rate['rate']

    rate = rate if rate > 0 else user.rate
    review_rate = review_rate if review_rate > 0 else user.review_rate
    hourly_rate = hourly_rate if hourly_rate > 0 else user.hourly_rate

    return rate, review_rate, hourly_rate


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

    def html2pdf(self, html_filename, pdf_filename):
        html2pdf_js = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                   '../../', 'html2pdf.js')
        self.stdout.write("Saving PDF to '%s'" % pdf_filename)
        result = call([settings.POOTLE_INVOICES_PHANTOMJS_BIN, html2pdf_js,
                       html_filename, pdf_filename])
        if result:
            self.stdout.write('Script returned result: %s' % result)

    def is_pdf_renderer_configured(self):
        phantomjs_bin = settings.POOTLE_INVOICES_PHANTOMJS_BIN
        if phantomjs_bin is None or not os.path.exists(phantomjs_bin):
            return False
        return True

    def send_invoice(self, subject, to, cc, bcc, html, pdf_filepath):
        # set non-empty body according
        # http://stackoverflow.com/questions/14580176/confusion-with-sending-email-in-django
        mail = EmailMultiAlternatives(subject=subject, body=strip_tags(html),
                                      to=to, cc=cc, bcc=bcc)
        mail.attach_alternative(html, 'text/html')
        if pdf_filepath is not None:
            mail.attach_file(pdf_filepath, 'application/pdf')
        self.stdout.write("Sending email to %s" % to)
        # FIXME: reuse connections to the mail server
        # (http://stackoverflow.com/a/10215091/783019)
        if mail.send() > 0:
            self.stdout.write("Email sent")
        else:
            self.stdout.write("ERROR: sending failed")

    def handle(self, **options):
        can_generate_pdfs = self.is_pdf_renderer_configured()
        if not can_generate_pdfs:
            logger.warn(
                'NOTICE: settings.POOTLE_INVOICES_PHANTOMJS_BIN not defined or'
                'nothing found in the specified path. PDFs will not be generated.'
            )

        month = options['month']
        add_correction = False
        if month is None:
            month = get_previous_month()
            add_correction = True

        if not is_valid_month(month):
            raise CommandError(
                '--month parameter has an invalid format: "%s", '
                'while it should be in "YYYY-MM" format'
                % month
            )

        now = timezone.now()
        [start, end] = get_date_interval(month)
        date = end if now > end else now

        month_dir = os.path.join(settings.POOTLE_INVOICES_DIRECTORY, month)
        if not os.path.exists(month_dir):
            os.makedirs(month_dir)

        users = settings.POOTLE_INVOICES_RECIPIENTS.items()
        if options['user_list']:
            users = filter(lambda x: x[0] in options['user_list'], users)

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
            translated_words = 0
            reviewed_words = 0
            hours = 0
            correction = 0

            usernames = (username, ) + user_conf.get('subcontractors', ())
            main_username = username

            for username in usernames:
                self.stdout.write('Getting data for %s' % username)
                user = user_dict[username]
                if main_username == username:
                    main_user = user
                    rate, review_rate, hourly_rate = \
                        get_rates(main_user, start, end)

                scores = ScoreLog.objects.for_user_in_range(user, start, end)
                scores = scores.order_by(SCORE_TRANSLATION_PROJECT)
                for row in get_grouped_word_stats(scores):
                    translated_words += row['translated']
                    reviewed_words += row['reviewed']

                tasks = PaidTask.objects.for_user_in_range(user, start, end)
                for task in tasks:
                    if task.task_type == PaidTaskTypes.TRANSLATION:
                        translated_words += task.amount
                    elif task.task_type == PaidTaskTypes.REVIEW:
                        reviewed_words += task.amount
                    elif task.task_type == PaidTaskTypes.HOURLY_WORK:
                        hours += task.amount
                    elif task.task_type == PaidTaskTypes.CORRECTION:
                        correction += task.amount

            translated_words = int(round(translated_words))
            reviewed_words = int(round(reviewed_words))

            translation_amount = round(translated_words * rate, 2)
            review_amount = round(reviewed_words * review_rate, 2)
            hours_amount = round(hours * hourly_rate, 2)

            balance = None
            total = translation_amount + review_amount + hours_amount + correction

            minimal_payment = user_conf.get('minimal_payment', 0)
            correction_added = False

            if add_correction and total > 0 and total < minimal_payment:
                first_moment = now.replace(day=1, hour=0, minute=0, second=0,
                                           tzinfo=timezone.get_default_timezone())
                PaidTask.objects.create(
                    task_type=PaidTaskTypes.CORRECTION,
                    amount=(-1) * total,
                    rate=1,
                    datetime=end,
                    description='Carryover to the next month',
                    user=user,
                )
                PaidTask.objects.create(
                    task_type=PaidTaskTypes.CORRECTION,
                    amount=total,
                    rate=1,
                    datetime=first_moment,
                    description='Carryover from the previous month',
                    user=user,
                )
                correction_added = True
                balance = total
                total = 0

            extra_amount = 0
            if 'extra_add' in user_conf and total > 0:
                extra_amount += user_conf['extra_add']
            if 'extra_multiply' in user_conf:
                extra_amount += total * (user_conf['extra_multiply'] - 1)

            id = user_conf['invoice_prefix'] + month

            total += extra_amount

            ctx = {
                'total': total,
                'extra_amount': extra_amount,

                'translated_words': translated_words,
                'reviewed_words': reviewed_words,
                'hours_count': hours,
                'correction': correction,

                'translation_amount': translation_amount,
                'review_amount': review_amount,
                'hours_amount': hours_amount,

                'id': id,
                'user': main_user,
                'date': date,
                'month': start,
                'rate': rate,
                'review_rate': review_rate,
                'hourly_rate': hourly_rate,

                'correction_added': correction_added,
                'balance': balance,
            }
            ctx.update(user_conf)
            ctx.update({
                'wire_info': user_conf['wire_info'].lstrip(),
                'paid_by': user_conf['paid_by'].lstrip(),
            })

            fullname = user_conf['name']

            filename = os.path.join(
                month_dir,
                u'Invoice - %s - %s' % (fullname, id),
            )

            html_filename = filename + '.html'
            pdf_filename = filename + '.pdf'

            self.stdout.write("Saving HTML to '%s'" % html_filename)
            html = render_to_string('invoices/invoice.html', ctx)
            codecs.open(html_filename, 'w', 'utf-8').write(html)
            if can_generate_pdfs:
                self.html2pdf(html_filename, pdf_filename)

            if not options['send_emails']:
                continue

            if 'accounting-email' not in user_conf:
                logger.warning(
                    '`accounting_email` not found in configuration for '
                    'user %s. Sending email will be skipped for this user.',
                    username,
                )
                continue

            debug_email_list = options['debug_email_list']
            bcc_email_list = options['bcc_email_list']
            ctx.update({
                'debug_emails': debug_email_list,
                'bcc_email_list': bcc_email_list,
            })

            to_email_list = user_conf['accounting-email'].split(',')
            cc_email_list = None
            if 'accounting-email-cc' in user_conf:
                cc_email_list = user_conf['accounting-email-cc'].split(',')

            if total > 0:
                subject = u'For payment: Invoice %s, %s' % (id, fullname)
                to = debug_email_list or to_email_list
                cc = None if debug_email_list else cc_email_list

                ctx.update({
                    'accounting': True,
                    'to_email_list': to_email_list,
                    'cc_email_list': cc_email_list,
                })
                html = render_to_string('invoices/invoice_message.html', ctx)
                self.send_invoice(subject, to, cc, bcc_email_list, html,
                                  pdf_filename)

            to_email_list = user_conf['email'].split(',')
            cc_email_list = None

            if total > 0:
                html = render_to_string('invoices/invoice_message.html', ctx)
                subject = u'Sent for payment: Invoice %s, %s' % (id, fullname)
            else:
                subject = (
                    u'Notice: No payment will be sent this month to %s'
                    % fullname
                )
                ctx.update({
                    'accounting': False,
                    'to_email_list': to_email_list,
                    'cc_email_list': cc_email_list,
                })
                html = render_to_string('invoices/no_invoice_message.html', ctx)
                pdf_filename = None
                if correction_added:
                    subject += u"; unpaid balance carried over to next month"

            to = debug_email_list or to_email_list
            self.send_invoice(subject, to, None, bcc_email_list, html,
                              pdf_filename)
