# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os

from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.utils.lru_cache import lru_cache

from pootle_misc.util import get_date_interval
from pootle_statistics.models import ScoreLog

from ..generators import HTMLGenerator, PDFGenerator
from ..utils import get_grouped_word_stats

from .paidtask import PaidTask, PaidTaskTypes
from .payment_email import (AccountingPaymentEmail, UserNoPaymentEmail,
                            UserPaymentEmail)


logger = logging.getLogger(__name__)


GENERATOR_MODULES = (HTMLGenerator, PDFGenerator)


MONTH_FORMAT = '%Y-%m'


def get_previous_month():
    """Returns the previous month as a datetime object."""
    return timezone.now().replace(day=1) - timedelta(days=1)


class Invoice(object):

    required_config_fields = (
        ('name', 'paid_by', 'wire_info'),  # Core fields
        ('email', 'accounting_email'),  # Email-related fields
    )

    def __init__(self, user, config, month=None, subcontractors=None,
                 add_correction=False):
        self.user = user
        self.conf = config
        self.subcontractors = [] if subcontractors is None else subcontractors
        self.add_correction = add_correction

        self.month = get_previous_month() if month is None else month
        (month_start, month_end) = get_date_interval(self.month_string)
        self.month_start = month_start
        self.month_end = month_end
        self.now = timezone.now()

        # Holds a list of tuples with generated file paths and their media types
        self.files = []
        self.generators = (
            Mod() for Mod in GENERATOR_MODULES if Mod.is_configured()
        )

    def __repr__(self):
        return u'<Invoice %s:%s>' % (self.user.username, self.month_string)

    @classmethod
    def check_config_for(cls, config_dict, username, require_email_fields=False):
        """Ensures the invoice configuration dictionary `config_dict` contains
        the required fields.

        :param username: Username owning the configuration.
        :param validate_email: Whether to also require email-related fields.
        """
        required_fields = (
            list(sum(cls.required_config_fields, ())) if require_email_fields else
            cls.required_config_fields[0]
        )
        missing_required_fields = [
            field for field in required_fields
            if field not in config_dict
        ]
        if len(missing_required_fields) > 0:
            raise ImproperlyConfigured(
                'The configuration for user %s is missing the following required '
                'fields: %s.\n'
                'Please double-check your configuration.'
                % (username, u', '.join(missing_required_fields))
            )

        return config_dict

    @property
    def id(self):
        return self.conf.get('invoice_prefix', '') + self.month_string

    @property
    def month_string(self):
        return self.month.strftime(MONTH_FORMAT)

    @lru_cache()
    def get_rates(self):
        """Get user rates that were set for the current user during the current
        month  from start to end. Raise an exception if the user has multiple
        rates during the period.

        :return: a tuple ``(rate, review_rate, hourly_rate)`` where ``rate`` is
            the translation rate, and ``review_rate`` is the review rate, and
            ``hourly_rate`` is the rate for hourly work that can be added as
            PaidTask.
        """
        scores = ScoreLog.objects.for_user_in_range(self.user, self.month_start,
                                                    self.month_end)
        rates = scores.values('rate', 'review_rate').distinct()
        if len(rates) > 1:
            raise ValueError('Multiple rate values recorded for user %s.' %
                             (self.user.username))

        rate = rates[0]['rate'] if len(rates) == 1 else 0
        review_rate = rates[0]['review_rate'] if len(rates) == 1 else 0
        hourly_rate = 0

        tasks = PaidTask.objects.for_user_in_range(self.user, self.month_start,
                                                   self.month_end)
        task_rates = tasks.values('task_type', 'rate').distinct()
        for task_rate in task_rates:
            if (task_rate['task_type'] == PaidTaskTypes.TRANSLATION and
                rate > 0 and
                task_rate['rate'] != rate):
                raise ValueError('Multiple TRANSLATION rate values for user %s.'
                                 % self.user.username)
            if (task_rate['task_type'] == PaidTaskTypes.REVIEW and
                review_rate > 0 and
                task_rate['rate'] != review_rate):
                raise ValueError('Multiple REVIEW rate values for user %s.' %
                                 self.user.username)
            if task_rate['task_type'] == PaidTaskTypes.HOURLY_WORK:
                if hourly_rate > 0 and task_rate['rate'] != hourly_rate:
                    raise ValueError('Multiple HOURLY_WORK rate values for user %s.'
                                     % self.user.username)
                hourly_rate = task_rate['rate']

        rate = rate if rate > 0 else self.user.rate
        review_rate = review_rate if review_rate > 0 else self.user.review_rate
        hourly_rate = hourly_rate if hourly_rate > 0 else self.user.hourly_rate

        return rate, review_rate, hourly_rate

    @lru_cache()
    def get_total_amounts(self):
        """Calculates and returns the total amounts for the invoice's user and
        month.
        """
        (translated_words, reviewed_words,
         hours, correction) = self._get_full_user_amounts(self.user)

        translated_words = int(round(translated_words))
        reviewed_words = int(round(reviewed_words))

        translation_rate, review_rate, hourly_rate = self.get_rates()

        translation_amount = round(translated_words * translation_rate, 2)
        review_amount = round(reviewed_words * review_rate, 2)
        hours_amount = round(hours * hourly_rate, 2)

        subtotal = translation_amount + review_amount + hours_amount + correction

        if self.should_add_correction(subtotal):
            extra_amount = 0
            balance = subtotal
            total = 0
        else:
            extra_amount = (self.conf['extra_add']
                            if 'extra_add' in self.conf and subtotal > 0
                            else 0)
            balance = None
            total = subtotal + extra_amount

        return {
            'subtotal': subtotal,
            'extra_amount': extra_amount,
            'total': total,
            'balance': balance,

            'translated_words': translated_words,
            'reviewed_words': reviewed_words,
            'hours_count': hours,
            'correction': correction,

            'translation_amount': translation_amount,
            'review_amount': review_amount,
            'hours_amount': hours_amount,
        }

    def _get_full_user_amounts(self, user):
        """Returns a tuple with the number of translated and reviewed words, as
        well as the hours and the applicable correction for `user` in the
        invoice's month. This includes subcontractors' amounts too.
        """
        (translated_words, reviewed_words,
         hours, correction) = self._get_user_amounts(self.user)
        for subcontractor in self.subcontractors:
            (subc_translated_words, subc_reviewed_words,
             subc_hours, subc_correction) = self._get_user_amounts(subcontractor)
            translated_words += subc_translated_words
            reviewed_words += subc_reviewed_words
            hours += subc_hours
            correction += subc_correction

        return (translated_words, reviewed_words, hours, correction)

    def _get_user_amounts(self, user):
        """Returns a tuple with the number of translated and reviewed words, as
        well as the hours and the applicable correction for `user` in the
        invoice's month.
        """
        translated_words = reviewed_words = hours = correction = 0

        scores = ScoreLog.objects.for_user_in_range(user, self.month_start,
                                                    self.month_end)
        scores = scores.order_by('submission__translation_project')
        for row in get_grouped_word_stats(scores):
            translated_words += row['translated']
            reviewed_words += row['reviewed']

        tasks = PaidTask.objects.for_user_in_range(user, self.month_start,
                                                   self.month_end)
        for task in tasks:
            if task.task_type == PaidTaskTypes.TRANSLATION:
                translated_words += task.amount
            elif task.task_type == PaidTaskTypes.REVIEW:
                reviewed_words += task.amount
            elif task.task_type == PaidTaskTypes.HOURLY_WORK:
                hours += task.amount
            elif task.task_type == PaidTaskTypes.CORRECTION:
                correction += task.amount

        return (translated_words, reviewed_words, hours, correction)

    def should_add_correction(self, subtotal):
        """Returns `True` if given the `subtotal` amount a carry-over correction
        should be added to this invoice.
        """
        return (self.add_correction and
                subtotal > 0 and
                subtotal < self.conf.get('minimal_payment', 0))

    def _add_correction(self, total_amount):
        """Adds a correction for the value of `total_amount` in the month being
        processed.
        """
        initial_moment = self.now.replace(day=1, hour=0, minute=0, second=0,
                                          tzinfo=timezone.get_default_timezone())
        PaidTask.objects.create(
            task_type=PaidTaskTypes.CORRECTION,
            amount=(-1) * total_amount,
            rate=1,
            datetime=self.month_end,
            description='Carryover to the next month',
            user=self.user,
        )
        PaidTask.objects.create(
            task_type=PaidTaskTypes.CORRECTION,
            amount=total_amount,
            rate=1,
            datetime=initial_moment,
            description='Carryover from the previous month',
            user=self.user,
        )

    def get_context_data(self):
        translation_rate, review_rate, hourly_rate = self.get_rates()

        ctx = {
            'id': self.id,
            'user': self.user,
            'date': self.month_end if self.now > self.month_end else self.now,
            'month': self.month_start,

            'rate': translation_rate,
            'review_rate': review_rate,
            'hourly_rate': hourly_rate,
        }

        amounts = self.get_total_amounts()
        ctx.update(amounts)
        ctx.update({
            'correction_added': self.should_add_correction(amounts['subtotal']),
        })
        ctx.update(self.conf)
        ctx.update({
            'wire_info': self.conf['wire_info'].lstrip(),
            'paid_by': self.conf['paid_by'].lstrip(),
        })

        return ctx

    def get_filename(self):
        # FIXME: make this configurable
        return u'Invoice - %s - %s' % (self.conf['name'], self.id)

    def get_filepath(self, extension):
        """Returns the absolute file path for the invoice, using `extension` as
        a file extension.
        """
        month_dir = os.path.join(settings.POOTLE_REPORTS_INVOICES_DIRECTORY,
                                 self.month_string)
        if not os.path.exists(month_dir):
            os.makedirs(month_dir)

        return os.path.join(month_dir, u'.'.join([self.get_filename(), extension]))

    def _write_to_disk(self):
        """Write the invoice to disk using all available generators.

        :return: a list of two-tuples which contain the absolute path to the
            generated file, and their media type.
        """
        generated_files = []
        ctx = self.get_context_data()
        for generator in self.generators:
            filepath = self.get_filepath(generator.extension)
            logger.info('Generating %s at "%s"...' % (generator.name, filepath))
            success = generator.generate(filepath, ctx)
            if success:
                generated_files.append((filepath, generator.media_type))

        return generated_files

    def generate(self):
        """Calculates invoices' amounts and generates the invoices on disk.

        * Side-effect: this method writes a correction if the total amount is
            below the minimum stipulated.
        * Side-effect: this method populates the object's `files` member.
        """
        amounts = self.get_total_amounts()
        if self.should_add_correction(amounts['subtotal']):
            self._add_correction(amounts['subtotal'])

        self.files = self._write_to_disk()

    def send_by_email(self, override_to=None, override_bcc=None):
        """Sends the invoice by email.

        :param override_to: Optionally override configured message recipients.
        :param override_bcc: Bcc recipients.

        :return: The number of successfully delivered messages
        """
        ctx = self.get_context_data()

        amounts = self.get_total_amounts()
        if amounts['total'] <= 0:
            return UserNoPaymentEmail(self.id, self.conf, ctx,
                                      override_to=override_to,
                                      override_bcc=override_bcc).send()

        attachments = [file[0] for file in self.files if 'html' not in file[1]]
        count = 0
        count += UserPaymentEmail(self.id, self.conf, ctx,
                                  override_to=override_to,
                                  override_bcc=override_bcc,
                                  attachments=attachments).send()
        count += AccountingPaymentEmail(self.id, self.conf, ctx,
                                        override_to=override_to,
                                        override_bcc=override_bcc,
                                        attachments=attachments).send()
        return count
