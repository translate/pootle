#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Evernote Corporation
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

from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import Resolver404, resolve, reverse
from django.dispatch import receiver
from django.shortcuts import redirect, render
from django.utils.http import urlquote, urlencode
from django.utils.translation import ugettext as _

from pootle.core.url_helpers import urljoin
from pootle_profile.views import login, redirect_after_login

from .backends.evernote import EvernoteBackend


def sso_callback(request, redirect_to):
    """Callback function run after a user has successfully signed on with
    Evernote.

    This runs the authentication mechanisms and creates any necessary
    accounts.
    """
    redirect_to = urljoin('', '', redirect_to)
    create_account = 'create' in request.GET
    user = None

    try:
        user = auth.authenticate(request=request,
                                 create_account=create_account)

        if user is not None:
            auth.login(request, user)
            return redirect_after_login(request, redirect_to)
    except EvernoteBackend.CookieExpired:
        redirect_url = '?'.join([
            reverse('en-auth-sso-login'),
            urlencode({auth.REDIRECT_FIELD_NAME: redirect_to}),
        ])
        return redirect(redirect_url)
    except EvernoteBackend.AlreadyLinked:
        messages.error(request,
                       _("Cannot link: your Evernote account is already "
                         "linked with another Pootle account."))
        return redirect(redirect_to)

    # No user-account exists, offer to link it
    redirect_url = '?'.join([
        reverse('en-auth-account-link'),
        urlencode({auth.REDIRECT_FIELD_NAME: redirect_to}),
    ])
    return redirect(redirect_url)


def sso_login(request):
    """Redirects users to the Evernote SSO page."""
    redirect_to = request.REQUEST.get(auth.REDIRECT_FIELD_NAME,
                                      reverse('pootle-home'))

    if (request.user.is_authenticated() and
        hasattr(request.user, 'evernote_account')):
        return redirect_after_login(request)

    return_path = reverse('en-auth-sso-callback', args=[redirect_to])
    if 'create' in request.GET:
        return_path = '{0}?create'.format(return_path)

    sso_url = urljoin(settings.EN_SSO_BASE, settings.EN_SSO_PATH,
                      settings.EN_SSO_SERVER_ALIAS, urlquote(return_path))

    return redirect(sso_url)


def link(request):
    """Logs the Pootle user in and links the account with Evernote."""
    return login(request, template_name='auth/link_with_evernote.html')


@receiver(auth.user_logged_in)
def create_evernote_account(sender, request, user, **kwargs):
    """Triggers a new `EvernoteAccount` creation once the user has
    logged-in to link its account with Evernote.

    The only situations where an account creation must be requested are:
        - when the Evernote auth backend has been used
        - when the user requested to link its user-account with Evernote
    """
    try:
        match = resolve(request.path_info)
        requested_to_link = match.url_name == 'en-auth-account-link'
    except Resolver404:
        requested_to_link = False

    if user.backend.endswith('EvernoteBackend') or requested_to_link:
        auth.authenticate(request=request, create_account=True)


@login_required
def account_info(request):
    return render(request, 'profiles/settings/evernote_account.html')


@login_required
def unlink(request):
    """Removes current user's link with its Evernote account."""
    if hasattr(request.user, 'evernote_account'):
        ea = request.user.evernote_account
        if not ea.user_autocreated:
            ea.delete()

    return redirect('en-auth-account-info')
