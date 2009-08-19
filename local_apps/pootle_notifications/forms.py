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

from django.forms import ModelForm
from django import forms
from django.contrib.contenttypes.models import ContentType

from pootle_notifications.models import Notices
from pootle_app.models import Language, TranslationProject

class LanguageNoticeForm(ModelForm):
    content = ContentType.objects.get(model='language')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())
    object_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Notices

    def set_initial_value(self, code):
        language = Language.objects.get(code = code);
        self.fields['object_id'].initial = language.id


class TransProjectNoticeForm(ModelForm):
    content = ContentType.objects.get(model='translationproject')
    content_type = forms.ModelChoiceField(initial=content.id, queryset=ContentType.objects.all(),
                         widget=forms.HiddenInput())

    object_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Notices

    def set_initial_value(self, language_code, project_code):
        transproj = TranslationProject.objects.get(language__code=language_code, project__code=project_code)
        self.fields['object_id'].initial = transproj.id
