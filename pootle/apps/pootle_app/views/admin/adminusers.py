#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django import forms
from django.contrib.auth import get_user_model
from django.forms.models import BaseModelFormSet
from django.utils.translation import ugettext as _

from pootle.core.decorators import admin_required
from pootle_app.views.admin import util


User = get_user_model()


@admin_required
def view(request):
    fields = ("username", "full_name", "email", "is_active", "is_superuser")
    queryset = User.objects.hide_defaults().order_by('username')
    return util.edit(request, 'admin/users.html', User, fields=fields,
                     formset=BaseUserFormSet, queryset=queryset,
                     can_delete=True)


class BaseUserFormSet(BaseModelFormSet):
    """This formset deals with user admininistration. We have to add a
    password field so that the passwords of users can be set.

    We override the save_existing and save_new formset methods so that
    we can 1) yank out the password field before the formset attempts
    to save the field 'set_password' (which would fail anyway, since
    the User model has no such field) and 2) set the password for an
    object once it has been saved.
    """

    def add_fields(self, form, index):
        super(BaseUserFormSet, self).add_fields(form, index)
        form.fields["set_password"] = forms.CharField(required=False, label=_("Password"), widget=forms.PasswordInput())

    def del_field(self, form):
        password = form['set_password'].data
        del form.fields['set_password']
        return password

    def save_extra(self, instance, password, commit=True):
        """process fields that require behavior different from model default"""
        changed = False
        # don't store plain text password, use set_password method to
        # set encrypted password
        if password != '':
            instance.set_password(password)
            changed = True

        if commit and changed:
            instance.save()

        return instance

    def save_existing(self, form, instance, commit=True):
        password = self.del_field(form)
        return self.save_extra(super(BaseUserFormSet, self).save_existing(form, instance, commit), password, commit)

    def save_new(self, form, commit=True):
        password = self.del_field(form)
        return self.save_extra(super(BaseUserFormSet, self).save_new(form, commit), password, commit)
