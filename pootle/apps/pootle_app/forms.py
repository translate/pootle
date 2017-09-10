# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import re
import urlparse
from collections import OrderedDict

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model

from pootle.i18n.gettext import ugettext_lazy as _
from pootle_fs.delegate import fs_plugins
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store


LANGCODE_RE = re.compile("^[a-z]{2,}([_-]([a-z]{2,}|[0-9]{3}))*(@[a-z0-9]+)?$",
                         re.IGNORECASE)


class LanguageForm(forms.ModelForm):

    specialchars = forms.CharField(strip=False, required=False)

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

    def clean_specialchars(self):
        """Ensures inputted characters are unique."""
        chars = self.cleaned_data['specialchars']
        return u''.join(
            OrderedDict((char, None) for char in list(chars)).keys()
        )


class ProjectForm(forms.ModelForm):

    source_language = forms.ModelChoiceField(queryset=Language.objects.none())
    fs_plugin = forms.ChoiceField(choices=[])

    class Meta(object):
        model = Project
        fields = ('id', 'code', 'fullname', 'checkstyle',
                  'filetypes', 'fs_plugin', 'source_language', 'ignoredfiles',
                  'report_email', 'screenshot_search_prefix', 'disabled',)

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)

        queryset = Language.objects.exclude(code='templates')
        self.fields['source_language'].queryset = queryset

        self.fields["filetypes"].initial = [
            self.fields["filetypes"].queryset.get(name="po")]
        self.fields["fs_plugin"].choices = [(x, x) for x in fs_plugins.gather()]

    def clean_filetypes(self):
        value = self.cleaned_data.get('filetypes', [])
        if not self.instance.pk:
            return value
        for filetype in self.instance.filetypes.all():
            if filetype not in value:
                has_stores = Store.objects.filter(
                    translation_project__project=self.instance, filetype=filetype)
                if has_stores.exists():
                    raise forms.ValidationError(
                        _("You cannot remove a file type from a Project, "
                          "if there are files of that file type ('%s')"
                          % filetype))
        return value

    def clean_fullname(self):
        return self.cleaned_data['fullname'].strip()

    def clean_code(self):
        return self.cleaned_data['code'].strip()

    def save(self, commit=True):
        created = bool(not self.instance.pk)
        project = super(ProjectForm, self).save(commit=commit)
        project.config["pootle_fs.fs_type"] = self.cleaned_data["fs_plugin"]
        if created and self.cleaned_data["fs_plugin"] == "localfs":
            project.config["pootle_fs.fs_url"] = os.path.join(
                settings.POOTLE_TRANSLATION_DIRECTORY,
                project.code)
        return project


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


class PermissionsUsersSearchForm(forms.Form):
    q = forms.CharField(max_length=255)

    def __init__(self, *args, **kwargs):
        self.directory = kwargs.pop("directory")
        super(PermissionsUsersSearchForm, self).__init__(*args, **kwargs)

    def search(self):
        existing_permission_users = (
            self.directory.permission_sets.values_list("user"))
        users = get_user_model().objects.exclude(
            pk__in=existing_permission_users)
        return dict(
            results=[
                dict(id=int(m["id"]), text=m["username"])
                for m
                in (users.filter(username__contains=self.cleaned_data["q"])
                         .values("id", "username").order_by("username"))])
