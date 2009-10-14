#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

"""This view defines the home / account pages for a user."""

from django.forms import ModelForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from django.shortcuts import render_to_response
from django.template import RequestContext 
from django.contrib.auth.decorators import login_required
from django.forms.fields import email_re
from django.forms.util import ErrorList

from pootle_misc.baseurl import redirect

def is_valid_email(email):
    return (email_re.match(email) is not None)

class UserForm(ModelForm):

    def clean(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data.get("email")

        if not email or not is_valid_email(email):
            msg = _('* Not a valid e-mail address.')
            self._errors["email"] = ErrorList([msg])

        # Always return the full collection of cleaned data.
        return cleaned_data

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

@login_required
def edit_personal_info(request):
    if request.POST:
        post = request.POST.copy()
        user_form = UserForm(post, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            response = redirect('/accounts/'+request.user.username)
    else:
        user_form = UserForm(instance=request.user)
    template_vars = { "form": user_form,}
    response = render_to_response('profiles/edit_personal.html', template_vars , context_instance=RequestContext(request))
    return response

