#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import iri_to_uri
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView, UpdateView

from pootle.core.views import LoginRequiredMixin
from pootle_misc.baseurl import redirect


User = auth.get_user_model()


class UserDetailView(TemplateView):
    template_name = 'profiles/profile_detail.html'

    def get_context_data(self, **kwargs):
        user = User.objects.get(username=kwargs['username'])

        return {
            'profile': user,
        }


class UserSettingsView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ('unit_rows', 'alt_src_langs')
    template_name = 'profiles/settings/profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_form(self, *args, **kwargs):
        form = super(UserSettingsView, self).get_form(*args, **kwargs)

        form.fields['alt_src_langs'].widget.attrs['class'] = \
            'js-select2 select2-multiple'
        form.fields['alt_src_langs'].widget.attrs['data-placeholder'] = \
            _('Select one or more languages')

        return form


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ('full_name', 'email')
    template_name = 'profiles/settings/personal.html'

    def get_object(self, queryset=None):
        return self.request.user


def redirect_after_login(request):
    redirect_to = request.REQUEST.get(auth.REDIRECT_FIELD_NAME, None)

    if not is_safe_url(url=redirect_to, host=request.get_host()):
        redirect_to = iri_to_uri(reverse('profiles_profile_detail',
                                 args=[request.user.username]))

    return redirect(redirect_to)


def login(request):
    """Log the user in."""
    if request.user.is_authenticated():
        return redirect_after_login(request)
    else:
        if request.POST:
            form = AuthenticationForm(request, data=request.POST)
            next = request.POST.get(auth.REDIRECT_FIELD_NAME, '')

            # Do login here.
            if form.is_valid():
                auth.login(request, form.get_user())

                language = request.POST.get('language')
                request.session['django_language'] = language

                return redirect_after_login(request)
        else:
            form = AuthenticationForm(request)
            next = request.GET.get(auth.REDIRECT_FIELD_NAME, '')

        context = {
            'form': form,
            'next': next,
        }

        return render_to_response("login.html", context,
                                  context_instance=RequestContext(request))


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/')
