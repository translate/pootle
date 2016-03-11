#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re
import urlparse

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from pootle_language.models import Language
from pootle_project.models import RESERVED_PROJECT_CODES, Project
from pootle_store.filetypes import filetype_choices
from pootle_store.models import Store


LANGCODE_RE = re.compile("^[a-z]{2,}([_-]([a-z]{2,}|[0-9]{3}))*(@[a-z0-9]+)?$",
                         re.IGNORECASE)


class LanguageForm(forms.ModelForm):

    class Meta(object):
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

    class Meta(object):
        model = Project
        fields = ('id', 'code', 'fullname', 'checkstyle', 'localfiletype',
                  'treestyle', 'source_language', 'ignoredfiles',
                  'report_email', 'screenshot_search_prefix', 'disabled',)

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)

        queryset = Language.objects.exclude(code='templates')
        self.fields['source_language'].queryset = queryset

        if self.instance.id:
            has_stores = Store.objects.filter(
                translation_project__project=self.instance
            ).count

            if has_stores:
                self.fields['localfiletype'].required = False

            if (self.instance.treestyle != 'auto' and
                self.instance.translationproject_set.count() and
                self.instance.treestyle == self.instance._detect_treestyle()):
                self.fields['treestyle'].required = False

    def clean_localfiletype(self):
        value = self.cleaned_data.get('localfiletype', None)
        if not value:
            value = self.instance.localfiletype
        filetypes = [x[0] for x in filetype_choices]
        if value not in filetypes:
            raise forms.ValidationError(
                "Unrecognised project filetype: %s" % value
            )
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
                _('"%s" cannot be used as a project code', value)
            )
        return value


class UserForm(forms.ModelForm):

    password = forms.CharField(label=_('Password'), required=False,
                               widget=forms.PasswordInput)

    class Meta(object):
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
