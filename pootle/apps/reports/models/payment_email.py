# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class BasePaymentEmail(object):
    """Base payment email class.

    :param override_to: Override list of message recipients.
    :param override_bcc: Override list of Bcc recipients.
    :param attachments: A list of tuples where elements are of the
        `(path_to_attachment, type)` shape.
    """

    template_name = 'invoices/invoice_message.html'

    def __init__(self, id, config, invoice_context, override_to=None,
                 override_bcc=None, attachments=None, **kwargs):
        self.id = id
        self.conf = config
        self.invoice_ctx = invoice_context
        self.override_to = override_to
        self.override_bcc = override_bcc
        self.attachments = attachments or []

    def get_recipient_list(self):
        return self.override_to or []

    def get_cc_list(self):
        return []

    def get_bcc_list(self):
        return self.override_bcc or []

    def get_subject(self):
        raise NotImplementedError('Children must implement `get_subject()`')

    def get_context_data(self):
        ctx = {
            'debug_emails': bool(self.override_to),
            'to_email_list': self.get_recipient_list(),
            'cc_email_list': self.get_cc_list(),
            'bcc_email_list': self.get_bcc_list(),
        }
        ctx.update(self.invoice_ctx)
        return ctx

    def get_body(self):
        """Returns the invoice's email body as a HTML string."""
        return render_to_string(self.template_name, self.get_context_data())

    def send(self):
        """Sends the payment email along with the invoice."""
        body = self.get_body()

        # Set non-empty body according to
        # http://stackoverflow.com/questions/14580176/confusion-with-sending-email-in-django
        mail = EmailMultiAlternatives(subject=self.get_subject(),
                                      body=strip_tags(body),
                                      to=self.get_recipient_list(),
                                      cc=self.get_cc_list(),
                                      bcc=self.get_bcc_list())
        mail.attach_alternative(body, 'text/html')

        for attachment in self.attachments:
            mail.attach_file(attachment[0], attachment[1])

        return mail.send()


class AccountingPaymentEmail(BasePaymentEmail):

    def get_recipient_list(self):
        return self.override_to or self.conf['accounting_email'].split()

    def get_cc_list(self):
        if self.override_to is not None:
            return []
        if 'accounting_email_cc' in self.conf:
            return self.conf['accounting_email_cc'].split()
        return []

    def get_subject(self):
        """Returns the subject of the email sent to accounting."""
        # FIXME: make this customizable
        ctx = self.get_context_data()
        return u'For payment: Invoice %s, %s' % (self.id, ctx['name'])

    def get_context_data(self):
        ctx = super(AccountingPaymentEmail, self).get_context_data()
        ctx.update({
            'accounting': True,
        })
        return ctx


class UserPaymentEmail(BasePaymentEmail):

    def get_recipient_list(self):
        return self.override_to or self.conf['email'].split()

    def get_subject(self):
        """Returns the subject of the email sent to the user."""
        # FIXME: make subjects customizable
        ctx = self.get_context_data()
        return u'Sent for payment: Invoice %s, %s' % (self.id, ctx['name'])

    def get_context_data(self):
        ctx = super(UserPaymentEmail, self).get_context_data()
        ctx.update({
            'accounting': False,
        })
        return ctx


class UserNoPaymentEmail(BasePaymentEmail):
    template_name = 'invoices/no_invoice_message.html'

    def get_recipient_list(self):
        return self.override_to or self.conf['email'].split()

    def get_subject(self):
        """Returns the subject of the email sent to the user."""
        # FIXME: make subjects customizable
        ctx = self.get_context_data()
        if ctx['correction_added']:
            return (
                u'Notice: No payment will be sent this month to %s'
                u'; unpaid balance carried over to next month' % ctx['name']
            )

        return (
            u'Notice: No payment will be sent this month to %s' % ctx['name']
        )
