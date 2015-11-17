# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.mail import get_connection, EmailMultiAlternatives


def send_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None,
              connection=None, html_message=None, headers=None):
    """Override django send_mail function to allow use of custom email headers.
    """

    connection = connection or get_connection(username=auth_user,
                                              password=auth_password,
                                              fail_silently=fail_silently)

    mail = EmailMultiAlternatives(subject, message,
                                  from_email, recipient_list,
                                  connection=connection, headers=headers)

    if html_message:
        mail.attach_alternative(html_message, 'text/html')

    return mail.send()
