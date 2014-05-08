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

import base64
import re
import time

from pyDes import triple_des, ECB

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.utils.http import urlencode
from django.views.decorators.cache import never_cache

from pootle.core.url_helpers import urljoin
from pootle_profile.views import login, redirect_after_login

from .models import EvernoteAccount


def get_cookie_dict(request):
    cookie = request.COOKIES.get(settings.EN_SSO_COOKIE, None)

    if cookie is not None:
        data = base64.b64decode(cookie)

        des3 = triple_des(settings.EN_SSO_SECRET_KEY, ECB)
        match = re.match(r'i=(?P<id>[0-9]+),'
                         r'u=(?P<name>[^,]+),'
                         r'e=(?P<email>[^,]+),'
                         r'x=(?P<expired>[0-9]+)',
                         des3.decrypt(data))

        if match:
            data = match.groupdict()
            if time.time() < data['expired']:
                return data

    return None


def sso_return_view(request, redirect_to='', create=0):
    redirect_to = urljoin('', '', redirect_to)

    data = get_cookie_dict(request)
    if data is None:
        redirect_url = '?'.join([
            reverse('evernote_login'),
            urlencode({auth.REDIRECT_FIELD_NAME: redirect_to}),
        ])
        return redirect(redirect_url)

    try:
        ea = EvernoteAccount.objects.get(evernote_id=data['id'])

        if request.user.is_authenticated():
            if request.user.id != ea.user.id:
                # it's not possible to link account with another user_id
                # TODO show error message
                return redirect(redirect_to)
        else:
            user = auth.authenticate(**{'evernote_account': ea})
            auth.login(request, user)
    except EvernoteAccount.DoesNotExist:
        if not create:
            redirect_url = '?'.join([
                reverse('evernote_login_link'),
                urlencode({auth.REDIRECT_FIELD_NAME: redirect_to}),
            ])
            return redirect(redirect_url)

        ea = EvernoteAccount(
            evernote_id=data['id'],
            email=data['email'],
            name=data['name'],
        )

        if request.user.is_authenticated():
            ea.user = request.user
        else:
            # create new Pootle user
            user = auth.authenticate(**{'evernote_account': ea})
            auth.login(request, user)

        ea.save()

    return redirect_after_login(request)


def evernote_login(request, create=0):
    redirect_to = request.REQUEST.get(auth.REDIRECT_FIELD_NAME, '')

    if not request.user.is_authenticated():
        if create:
            return sso_return_view(request, redirect_to, create)

        return_path = reverse('evernote_return', args=[redirect_to])
        sso_url = urljoin(settings.EN_SSO_BASE, settings.EN_SSO_PATH,
                          settings.EN_SSO_SERVER_ALIAS, return_path)
        return redirect(sso_url)

    if not hasattr(request.user, 'evernote_account'):
        return_path = reverse('evernote_create_return', args=[redirect_to])
        sso_url = urljoin(settings.EN_SSO_BASE, settings.EN_SSO_PATH,
                          settings.EN_SSO_SERVER_ALIAS, return_path)
        return redirect(sso_url)

    return redirect_after_login(request)


def evernote_login_link(request):
    """Logs the user in and links the account with Evernote."""
    return login(request, template_name='auth/link_with_evernote.html')


@receiver(auth.user_logged_in)
def create_evernote_account(sender, request, user, **kwargs):
    if not user.backend.endswith('EvernoteBackend'):
        return

    data = get_cookie_dict(request)
    if not data:
        return evernote_login(request, 1)

    # FIXME: shouldn't `get_or_create()` be enough?
    ea = EvernoteAccount.objects.filter(**{'evernote_id': data['id']})
    if len(ea) == 0:
        ea = EvernoteAccount(
            evernote_id=data['id'],
            email=data['email'],
            name=data['name']
        )
        ea.user = request.user
        ea.save()


@login_required
@never_cache
def evernote_account_info(request, context={}):
    return render_to_response('profiles/settings/evernote_account.html',
                              context, context_instance=RequestContext(request))


@login_required
def evernote_account_disconnect(request):
    if hasattr(request.user, 'evernote_account'):
        ea = request.user.evernote_account
        if not ea.user_autocreated:
            ea.delete()

    return redirect('evernote_account_link')
