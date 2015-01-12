#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
# Copyright 2013-2015 Evernote Corporation
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
import urlparse

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from pootle_language.models import Language
from pootle_project.models import Project, RESERVED_PROJECT_CODES
from pootle_store.models import Store


LANGCODE_RE = re.compile("^[a-z]{2,}([_-][a-z]{2,})*(@[a-z0-9]+)?$",
                         re.IGNORECASE)


class LanguageForm(forms.ModelForm):

    class Meta:
        model = Language
        fields = ('id', 'code', 'fullname', 'specialchars', 'nplurals',
                  'pluralequation',)

    def clean_code(self):
        if (not self.cleaned_data['code'] == 'templates' and
            not LANGCODE_RE.match(self.cleaned_data['code'])):
            raise forms.ValidationError(
                _('Language code does not follow the ISO convention')
            )

        return self.cleaned_data["code"]


class ProjectForm(forms.ModelForm):

    source_language = forms.ModelChoiceField(label=_('Source Language'),
                                             queryset=Language.objects.none())

    class Meta:
        model = Project
        fields = ('id', 'code', 'fullname', 'checkstyle', 'localfiletype',
                  'treestyle', 'source_language',  'report_email',
                  'screenshot_search_prefix', 'disabled',)

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)

        queryset = Language.objects.exclude(code='templates')
        self.fields['source_language'].queryset = queryset

        if self.instance.id:
            has_stores = Store.objects.filter(
                translation_project__project=self.instance
            ).count

            if has_stores:
                #self.fields['localfiletype'].widget.attrs['disabled'] = True
                self.fields['localfiletype'].required = False

            if (self.instance.treestyle != 'auto' and
                self.instance.translationproject_set.count() and
                self.instance.treestyle == self.instance._detect_treestyle()):
                #self.fields['treestyle'].widget.attrs['disabled'] = True
                self.fields['treestyle'].required = False

        def clean_localfiletype(self):
            value = self.cleaned_data.get('localfiletype', None)
            if not value:
                value = self.instance.localfiletype
            return value

        def clean_treestyle(self):
            value = self.cleaned_data.get('treestyle', None)
            if not value:
                value = self.instance.treestyle
            return value

        def clean_code(self):
            value = self.cleaned_data['code']
            if value in RESERVED_PROJECT_CODES:
                raise forms.ValidationError(
                    _('"%s" cannot be used as a project code' % value)
                )
            return value


class UserForm(forms.ModelForm):

    password = forms.CharField(label=_('Password'), required=False,
                               widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'is_active', 'full_name', 'email',
                  'is_superuser', 'twitter', 'linkedin', 'website', 'bio')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        # Require setting the password for new users
        if self.instance.pk is None:
            self.fields['password'].required = True

    def save(self, commit=True):
        password = self.cleaned_data['password']

        if password != '':
            user = super(UserForm, self).save(commit=False)
            user.set_password(password)

            if commit:
                user.save()
        else:
            user = super(UserForm, self).save(commit=commit)

        return user

    def clean_linkedin(self):
        url = self.cleaned_data['linkedin']
        if url != '':
            parsed = urlparse.urlparse(url)
            if 'linkedin.com' not in parsed.netloc or parsed.path == '/':
                raise forms.ValidationError(
                    _('Please enter a valid LinkedIn user profile URL.')
                )

        return url
