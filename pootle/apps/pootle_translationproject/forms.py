#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010-2013 Zuza Software Foundation
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

from django import forms
from django.utils.translation import ugettext as _

from pootle_app.models import Directory
from pootle_app.models.permissions import check_permission
from pootle_translationproject.models import TranslationProject


class DescriptionForm(forms.ModelForm):

    class Meta:
        model = TranslationProject


def upload_form_factory(request):
    translation_project = request.translation_project
    choices = []
    initial = 'suggest'

    if check_permission('overwrite', request):
        choices.append(('overwrite', _("Overwrite the current file if it "
                                       "exists")))
    if check_permission('translate', request):
        initial = 'merge'
        choices.append(('merge', _("Merge the file with the current file and "
                                   "turn conflicts into suggestions")))
    if check_permission('suggest', request):
        choices.append(('suggest', _("Add all new translations as "
                                     "suggestions")))

    class StoreFormField(forms.ModelChoiceField):
        def label_from_instance(self, instance):
            return instance.pootle_path[len(request.pootle_path):]

    class DirectoryFormField(forms.ModelChoiceField):
        def label_from_instance(self, instance):
            return instance.pootle_path[len(translation_project.pootle_path):]

    class UploadForm(forms.Form):
        file = forms.FileField(required=True, label=_('File'))
        overwrite = forms.ChoiceField(
            required=True,
            widget=forms.RadioSelect,
            label='',
            choices=choices,
            initial=initial
        )
        upload_to = StoreFormField(
            required=False,
            label=_('Upload to'),
            queryset=translation_project.stores.filter(
                pootle_path__startswith=request.pootle_path),
            help_text=_("Optionally select the file you want to merge with. "
                        "If not specified, the uploaded file's name is used.")
        )
        upload_to_dir = DirectoryFormField(
            required=False,
            label=_('Upload to'),
            queryset=Directory.objects.filter(
                pootle_path__startswith=translation_project.pootle_path). \
                exclude(pk=translation_project.directory.pk),
            help_text=_("Optionally select the file you want to merge with. "
                        "If not specified, the uploaded file's name is used.")
        )

    return UploadForm
