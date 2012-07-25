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

import locale

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django import forms

from pootle_app.models import Directory
from pootle_misc.baseurl import l
from pootle_language.models import Language
from pootle_project.models import Project


class Notice(models.Model):
    directory = models.ForeignKey('pootle_app.Directory', db_index=True)
    message = models.TextField(_('Message'))
    # Translators: The date that the news item was written
    added = models.DateTimeField(_('Added'), auto_now_add=True, null=True, db_index=True)

    def __unicode__(self):
        return self.message

    def get_absolute_url(self):
        return l(self.directory.pootle_path + 'notices/%d' % self.id)

    def get_date(self):
        return self.added.strftime(locale.nl_langinfo(locale.D_T_FMT))

    class Meta:
        ordering = ["-added"]


class NoticeForm(forms.Form):

    directory = forms.ModelChoiceField(queryset=Directory.objects.all(), widget=forms.HiddenInput)

    # Notice attributes
    message = forms.CharField(label=_('Message'), widget=forms.Textarea)
    publish_rss = forms.BooleanField(label=_('Publish on News feed'),required=False)
    send_email = forms.BooleanField(label=_('Send Email'), required=False)
    email_header = forms.CharField(label=_('Title'), required=False)
    restrict_to_active_users = forms.BooleanField(label=_('Email only to recently active users'), required=False)

    #project selection
    project_all = forms.BooleanField(label=_('All Projects'), required=False)
    project_selection = forms.ModelMultipleChoiceField(label=_("Project Selection"),
                                                       queryset=Project.objects.all(),
                                                       required=False)

    #language selection
    language_all = forms.BooleanField(label=_('All Languages'), required=False)
    language_selection = forms.ModelMultipleChoiceField(label=_("Language Selection"),
                                                        queryset=Language.objects.all(),
                                                        required=False)
