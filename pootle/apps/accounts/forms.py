# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.utils.translation import ugettext_lazy as _

from allauth.account import app_settings
from allauth.account.app_settings import AuthenticationMethod
from allauth.account.forms import LoginForm

from .utils import get_user_by_email


class SocialVerificationForm(LoginForm):

    def __init__(self, *args, **kwargs):
        self.sociallogin = kwargs.pop('sociallogin')
        super(SocialVerificationForm, self).__init__(*args, **kwargs)

        self.fields['login'].required = False

    def clean_login(self):
        # The plan is: let's gather the user based on the email information we
        # have available on the session, this way we don't have to fiddle
        # around customizing `user_credentials()`
        email = self.sociallogin.user.email

        if app_settings.AUTHENTICATION_METHOD == AuthenticationMethod.EMAIL:
            return email

        user = get_user_by_email(email)
        if user is not None:
            return user.username

        # Oops, something must be really broken if this stage is reached
        raise forms.ValidationError(
            _('Your user seems to have disappeared. Please report this '
              'to the site owners.')
        )
