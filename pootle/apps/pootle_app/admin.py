#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

import re

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from pootle_project.models import Project


### Project

class MyProjectAdminForm(forms.ModelForm):

    def clean_code(self):
        if re.search("[^a-zA-Z0-9_]", self.cleaned_data['code']):
            raise forms.ValidationError(_('Project code may only contain '
                                          'letters, numbers and _'))
        return self.cleaned_data["code"]

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'fullname', 'localfiletype')
    list_display_links = ('code', 'fullname')
    prepopulated_fields = {"fullname": ("code",)}
    radio_fields = {"treestyle": admin.VERTICAL}
    fieldsets = (
        (None, {
            'fields': ('code', 'fullname', 'localfiletype'),
        }),
        (_('Advanced Options'), {
            'classes': ('collapse',),
            'fields': ('treestyle', 'ignoredfiles'),
        }),
    )
    form = MyProjectAdminForm

admin.site.register(Project, ProjectAdmin)
