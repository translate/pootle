#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.dispatch import receiver

from allauth.account.signals import password_reset
from allauth.account.utils import perform_login


@receiver(password_reset)
def sign_user_in(sender, **kwargs):
    """Automatically signs the user in after a successful password reset.

    Implemented via signals because of django-allauth#735.
    """
    request = kwargs['request']
    user = kwargs['user']
    return perform_login(request, user, settings.ACCOUNT_EMAIL_VERIFICATION)
