# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import traceback

from django.shortcuts import render

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount import providers
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from pootle.middleware.errorpages import log_exception

from .utils import get_user_by_email
from .views import SocialVerificationView


class PootleSocialAccountAdapter(DefaultSocialAccountAdapter):

    def is_open_for_signup(self, request, sociallogin):
        """Controls whether signups are enabled on the site when using
        social authentication methods.
        """
        # Allauth's default behavior is to disallow creating *any* users if the
        # account adapter forbids so. In Pootle's case, the adapter's
        # `is_open_for_signup()` is controlled by
        # `settings.POOTLE_SIGNUP_ENABLED`, and we want to apply its semantics
        # only to regular user accounts, not social accounts. So social
        # accounts can sign up for new user accounts anytime.  If this is
        # considered to be problematic in the future, we might want to
        # introduce a new setting to control this, separate from
        # `POOTLE_SIGNUP_ENABLED`.
        return True

    def pre_social_login(self, request, sociallogin):
        """Hook to be run after receiving the OK from the social provider
        but before completing the social login process. At this time no
        new user accounts have been created and the user is still in the
        process of signing in. The provider has also pre-filled the user
        data in `sociallogin.user`.

        We'll use this hook to customize Allauth's default behavior so
        that sociallogin users reporting an email address that already
        exists in the system will need to verify they actually own the
        user account owning such email in Pootle.
        """
        email_address = sociallogin.user.email

        # There's a SocialAccount already for this login or the provider
        # doesn't share an email address: nothing to do here
        if sociallogin.user.pk is not None or not email_address:
            return

        # If there's already an existing email address on the system, we'll ask
        # for its connected user's password before proceeding.
        user = get_user_by_email(email_address)
        if user is not None:
            # Save `SocialLogin` instance for our custom view
            request.session['sociallogin'] = sociallogin.serialize()

            raise ImmediateHttpResponse(
                response=SocialVerificationView.as_view()(request)
            )

    def authentication_error(self, request, provider_id, error=None,
                             exception=None, extra_context=None):
        provider = providers.registry.by_id(provider_id)
        retry_url = provider.get_login_url(request,
                                           **dict(request.GET.iteritems()))

        tb = traceback.format_exc()
        log_exception(request, exception, tb)

        ctx = {
            'social_error': {
                'error': error,
                'exception': {
                    'name': exception.__class__.__name__,
                    'msg': unicode(exception),
                },
                'provider': provider.name,
                'retry_url': retry_url,
            },
        }
        raise ImmediateHttpResponse(
            response=render(request, 'account/social_error.html', ctx)
        )
