#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

import re

from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
from django.contrib import admin

from pootle_language.models import Language
from pootle_project.models import Project
from pootle_profile.models import PootleProfile


### Language
LANGCODE_RE = re.compile("^[a-z]{2,}([_-][a-z]{2,})*(@[a-z0-9]+)?$", re.IGNORECASE)
class MyLanguageAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(MyLanguageAdminForm, self).__init__(*args, **kwargs)
        self.fields['nplurals'].widget.attrs['class'] = \
            "js-select2 select2-nplurals"

    def clean_code(self):
        if not self.cleaned_data['code'] == 'templates' and not LANGCODE_RE.match(self.cleaned_data['code']):
            raise forms.ValidationError(_('Language code does not follow the ISO convention'))
        return self.cleaned_data["code"]


class LanguageAdmin(admin.ModelAdmin):
    list_display = ('code', 'fullname')
    list_display_links = ('code', 'fullname')
    fieldsets = (
        (None, {
            'fields': ('code', 'fullname', 'specialchars'),
        }),
        ('Plural information', {
            'fields': ('nplurals', 'pluralequation'),
        }),
    )
    form = MyLanguageAdminForm

admin.site.register(Language, LanguageAdmin)


### Project

class MyProjectAdminForm(forms.ModelForm):

    def clean_code(self):
        if re.search("[^a-zA-Z0-9_]", self.cleaned_data['code']):
            raise forms.ValidationError(_('Project code may only contain letters, numbers and _'))
        return self.cleaned_data["code"]

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'fullname', 'description', 'localfiletype')
    list_display_links = ('code', 'fullname')
    prepopulated_fields = {"fullname": ("code",)}
    radio_fields = {"treestyle": admin.VERTICAL}
    fieldsets = (
        (None, {
            'fields': ('code', 'fullname', 'description', 'localfiletype'),
        }),
        (_('Advanced Options'), {
            'classes': ('collapse',),
            'fields': ('treestyle', 'ignoredfiles'),
        }),
    )
    form = MyProjectAdminForm

admin.site.register(Project, ProjectAdmin)


### User / PootleProfile

admin.site.unregister(User)

class PootleProfileInline(admin.StackedInline):
    model = PootleProfile

class MyUserAdmin(UserAdmin):
    inlines = [PootleProfileInline]

admin.site.register(User, MyUserAdmin)
