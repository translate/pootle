#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django.core.mail import get_connection, EmailMultiAlternatives
from django.core.mail.message import EmailMessage


def send_mail(subject, message, from_email=None, recipient_list=[],
              bcc=[], cc=[], fail_silently=False, auth_user=None,
              auth_password=None, connection=None, html_message=False):
    """Wrapper around Django's :class:`~django.core.mail.message.EmailMessage`
    that accepts more fields than the defaults offered by
    :func:`~django.core.mail.send_mail`.

    :param subject: Subject of the email.
    :param message: Body of the email.
    :param from_email: Sender's address. If omitted,
                       :setting:`DEFAULT_FROM_EMAIL` is used.
    :param recipient_list: List of addresses used in the `To` header.
    :param bcc: List of addresses used in the `Bcc` header.
    :param cc: List of addresses used in the `Cc` header.
    :param fail_silently: Whether to invalidate exceptions raised when sending
                          mail.
    :param auth_user: Username used when authenticating the connection. If
                      unset, :setting:`EMAIL_HOST_USER` will be used.
    :param auth_password: Password used when authenticating the connection. If
                          unset, :setting:`EMAIL_HOST_PASSWORD` will be used.
    :param connection: An e-mail backend instance. Useful to reuse the same
                       connection for multiple messages. If unset, a new
                       connection will be created.
    :param html_message: Tells if `message` is formatted using HTML.
    """
    connection = connection or get_connection(username=auth_user,
                                              password=auth_password,
                                              fail_silently=fail_silently)
    if html_message:
        from lxml.html import fromstring, tostring
        # Get a plain text version of the HTML formatted message.
        text_content = tostring(fromstring(message), method='text')
        email_msg = EmailMultiAlternatives(subject, text_content, from_email,
                                           recipient_list, bcc=bcc, cc=cc,
                                           connection=connection)
        # Attach the HTML formatted message.
        email_msg.attach_alternative(message, "text/html")
        return email_msg.send()
    else:
        return EmailMessage(subject, message, from_email, recipient_list,
                            bcc=bcc, cc=cc, connection=connection).send()
