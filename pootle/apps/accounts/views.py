# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.shortcuts import redirect
from django.urls import reverse

from allauth.account.views import LoginView
from allauth.socialaccount.helpers import _add_social_account
from allauth.socialaccount.models import SocialLogin

from .forms import SocialVerificationForm


class SocialVerificationView(LoginView):
    form_class = SocialVerificationForm
    template_name = 'account/social_verification.html'

    def dispatch(self, request, *args, **kwargs):
        self.sociallogin = None
        data = request.session.get('sociallogin', None)
        if data is not None:
            self.sociallogin = SocialLogin.deserialize(data)

        if self.sociallogin is None:
            return redirect(reverse('account_login'))

        return super(SocialVerificationView, self).dispatch(request, *args,
                                                            **kwargs)

    def get_context_data(self, **kwargs):
        return {
            'email': self.sociallogin.user.email,
            'provider_name': self.sociallogin.account.get_provider().name,
        }

    def get_form_kwargs(self):
        kwargs = super(SocialVerificationView, self).get_form_kwargs()
        kwargs.update({
            'sociallogin': self.sociallogin,
        })
        return kwargs

    def form_valid(self, form):
        # Authentication is OK, log in and request to connect accounts
        form.login(self.request)
        return _add_social_account(self.request, self.sociallogin)
