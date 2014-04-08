#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation
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
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import iri_to_uri
from django.utils.http import is_safe_url, urlquote, urlencode

from pootle_misc.baseurl import redirect
from pootle_profile.forms import lang_auth_form_factory

from .models import EvernoteAccount


def get_cookie_dict(request):
    cookie = request.COOKIES.get(getattr(settings, 'SSO_COOKIE', ''))

    if cookie:
        data = base64.b64decode(cookie)

        des3 = triple_des(getattr(settings, 'SSO_SECRET_KEY', ''), ECB)
        match = re.match(
            r'i=(?P<id>[0-9]+),u=(?P<name>[^,]+),e=(?P<email>[^,]+),x=(?P<expired>[0-9]+)',
            des3.decrypt(data)
        )

        if match:
            d = match.groupdict()
            if time.time() < d['expired']:
                return d

    return None


def redirect_after_login(request, redirect_to):
    if not is_safe_url(url=redirect_to, host=request.get_host()):
        redirect_to = reverse('profiles_profile_detail',
                              args=[request.user.username])

    return redirect(redirect_to)


def sso_return_view(request, redirect_to='', create=0):
    redirect_to = '/%s' % redirect_to.lstrip('/')

    d = get_cookie_dict(request)
    if d:
        ea = EvernoteAccount.objects.filter(**{'evernote_id': d['id']})

        if len(ea) == 0:
            if not create:
                return redirect('/accounts/evernote/login/link?%s' %
                        urlencode({auth.REDIRECT_FIELD_NAME: redirect_to}))

            ea = EvernoteAccount(
                evernote_id = d['id'],
                email=d['email'],
                name=d['name']
            )

            if request.user.is_authenticated():
                ea.user = request.user
            else:
                # create new Pootle user
                user = auth.authenticate(**{'evernote_account': ea})
                auth.login(request, user)

            ea.save()

        else:
            ea = ea[0]

            if request.user.is_authenticated():
                if request.user.id != ea.user.id:
                    # it's not possible to link account with another user_id
                    # TODO show error message
                    return redirect(redirect_to)
            else:
                user = auth.authenticate(**{'evernote_account': ea})
                auth.login(request, user)

        return redirect_after_login(request, redirect_to)

    else:
        return redirect('/accounts/evernote/login/?%s' %
                        urlencode({auth.REDIRECT_FIELD_NAME: redirect_to}))


def evernote_login(request, create=0):
    redirect_to = request.REQUEST.get(auth.REDIRECT_FIELD_NAME, '')
    language = request.REQUEST.get('language')
    request.session['django_language'] = language

    script_name = (settings.SCRIPT_NAME and "%s/" %
                   settings.SCRIPT_NAME.rstrip('/').lstrip('/') or '')
    server_alias = getattr(settings, 'EVERNOTE_LOGIN_REDIRECT_SERVER_ALIAS' ,'')

    if not request.user.is_authenticated():
        if create:
            return sso_return_view(request, redirect_to, create)
        else:
            return redirect(
                getattr(settings, 'EVERNOTE_LOGIN_URL', '') +
                '%s/%saccounts/evernote/return/%s' %
                (server_alias, script_name, redirect_to.lstrip('/'))
            )
    else:
        if not hasattr(request.user, 'evernote_account'):
            return redirect(
                getattr(settings, 'EVERNOTE_LOGIN_URL', '') +
                '%s/%saccounts/evernote/create/return/%s' %
                (server_alias, script_name, redirect_to.lstrip('/'))
            )
        else:
            return redirect_after_login(request, redirect_to)


def evernote_login_link(request):
    """Logs the user in."""
    redirect_to = request.REQUEST.get(auth.REDIRECT_FIELD_NAME, '')

    if request.user.is_authenticated():
        return redirect_after_login(request, redirect_to)
    else:
        if request.POST:
            form = lang_auth_form_factory(request, data=request.POST)

            # Do login here
            if form.is_valid():
                auth.login(request, form.get_user())

                language = request.POST.get('language')
                request.session['django_language'] = language

                d = get_cookie_dict(request)
                if not d:
                    return evernote_login(request, 1)

                # FIXME: shouldn't `get_or_create()` be enough?
                ea = EvernoteAccount.objects.filter(**{'evernote_id': d['id']})
                if len(ea) == 0:
                    ea = EvernoteAccount(
                        evernote_id = d['id'],
                        email=d['email'],
                        name=d['name']
                    )
                    ea.user = request.user
                    ea.save()

                return redirect_after_login(request, redirect_to)
        else:
            form = lang_auth_form_factory(request)

        context = {
            'form': form,
            'next': request.REQUEST.get(auth.REDIRECT_FIELD_NAME, ''),
        }

        return render_to_response("auth/link_with_evernote.html", context,
                                  context_instance=RequestContext(request))


@login_required
def evernote_account_info(request, context={}):
    return render_to_response('profiles/settings/evernote_account.html',
                              context, context_instance=RequestContext(request))


@login_required
def evernote_account_disconnect(request):
    if hasattr(request.user, 'evernote_account'):
        ea = request.user.evernote_account
        if not ea.user_autocreated:
            ea.delete()

    return redirect('/accounts/evernote/link/')
