#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
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

from django import forms
from django.utils.translation import ugettext_lazy as _

from pootle_app.models import Directory
from pootle_notifications.models import Notice
from pootle_project.models import Project


def form_factory(current_directory):

    class _NoticeForm(forms.ModelForm):
        directory = forms.ModelChoiceField(
            queryset=Directory.objects.filter(pk=current_directory.pk),
            initial=current_directory.pk,
            widget=forms.HiddenInput(),
        )
        publish_rss = forms.BooleanField(
            label=_('Publish on news feed'),
            required=False,
            initial=True,
        )
        send_email = forms.BooleanField(
            label=_('Send email'),
            required=False,
        )
        email_header = forms.CharField(
            label=_('Title'),
            required=False,
        )
        restrict_to_active_users = forms.BooleanField(
            label=_('Email only to recently active users'),
            required=False,
            initial=True,
        )

        # Project selection
        if current_directory.is_language() or current_directory.is_root:
            project_all = forms.BooleanField(
                label=_('All Projects'),
                required=False,
            )
            project_selection = forms.ModelMultipleChoiceField(
                label=_("Project Selection"),
                queryset=Project.objects.all(),
                required=False,
                widget=forms.SelectMultiple(attrs={
                    'class': 'js-select2 select2-multiple',
                    'data-placeholder': _('Select one or more projects'),
                }),
            )

        # Language selection
        if current_directory.is_project() or current_directory.is_root:
            language_all = forms.BooleanField(
                label=_('All Languages'),
                required=False,
            )
            language_selection = forms.ModelMultipleChoiceField(
                label=_("Language Selection"),
                queryset=current_directory.project.languages,
                required=False,
                widget=forms.SelectMultiple(attrs={
                    'class': 'js-select2 select2-multiple',
                    'data-placeholder': _('Select one or more languages'),
                }),
            )

        class Meta:
            model = Notice

    return _NoticeForm
