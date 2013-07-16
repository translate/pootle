# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
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

from pootle_project.models import Project
from pootle_tagging.forms import TagForm
from pootle_translationproject.models import TranslationProject


class DescriptionForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ("fullname", "description", "report_target")


class TranslationProjectTagForm(TagForm):

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project')
        super(TranslationProjectTagForm, self).__init__(*args, **kwargs)

        self.fields['translation_project'] = forms.ModelChoiceField(
            label='',  # Blank label to don't see it.
            queryset=TranslationProject.objects.filter(project=project),
            widget=forms.Select(attrs={
                'id': 'js-tags-tp',
                # Use the 'hide' class to hide the field. The HiddenInput
                # widget renders a 'input' tag instead of a 'select' one and
                # that way the translation project can't be set.
                'class': 'hide',
            }),
        )
