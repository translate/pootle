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

from pootle_app.models import Language, Project
from pootle_app.models.profile import PootleProfile

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
from django.contrib import admin

import re


### Language

class LanguageAdmin(admin.ModelAdmin):
    list_display = ('code', 'fullname')
    list_display_links = ('code', 'fullname')
    fieldsets = (
        (None, {
            'fields': ('code', 'fullname', 'specialchars')
        }),
        ('Plural information', {
            'fields': ('nplurals', 'pluralequation')
        }),
    )

admin.site.register(Language, LanguageAdmin)


### Project

class MyProjectAdminForm(forms.ModelForm):

    def clean_code(self):
        if re.search("[^a-zA-Z0-9_]", self.cleaned_data['code']):
            raise forms.ValidationError('Project code may only contain letters, numbers and _')
        return self.cleaned_data["code"]

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'fullname', 'description', 'localfiletype')
    list_display_links = ('code', 'fullname')
    prepopulated_fields = {"fullname": ("code",)}
    radio_fields = {"treestyle": admin.VERTICAL}
    fieldsets = (
        (None, {
            'fields': ('code', 'fullname', 'description', 'localfiletype')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('createmofiles', 'treestyle', 'ignoredfiles')
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
