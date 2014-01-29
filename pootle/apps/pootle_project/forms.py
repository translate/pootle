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
from django.utils.translation import ugettext as _

from pootle_language.models import Language
from pootle_misc.forms import LiberalModelChoiceField
from pootle_project.models import Project
from pootle_tagging.forms import TagForm
from pootle_translationproject.models import TranslationProject


class DescriptionForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ("fullname", "description", "report_email")


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


class TranslationProjectFormSet(forms.models.BaseModelFormSet):

    def save_existing(self, form, instance, commit=True):
        result = super(TranslationProjectFormSet, self) \
                 .save_existing(form, instance, commit)
        form.process_extra_fields()
        return result

    def save_new(self, form, commit=True):
        result = super(TranslationProjectFormSet, self).save_new(form, commit)
        form.process_extra_fields()
        return result


def tp_form_factory(current_project):

    template_tp = current_project.get_template_translationproject()

    class TranslationProjectForm(forms.ModelForm):

        if template_tp is not None:
            update = forms.BooleanField(
                required=False,
                label=_("Update against templates"),
            )

        #FIXME: maybe we can detect if initialize is needed to avoid
        # displaying it when not relevant.
        #initialize = forms.BooleanField(required=False, label=_("Initialize"))

        project = forms.ModelChoiceField(
            queryset=Project.objects.filter(pk=current_project.pk),
            initial=current_project.pk,
            widget=forms.HiddenInput(),
        )
        language = LiberalModelChoiceField(
            label=_("Language"),
            queryset=Language.objects.exclude(
                translationproject__project=current_project
            ),
            widget=forms.Select(attrs={
                'class': 'js-select2 select2-language',
            }),
        )

        class Meta:
            prefix = "existing_language"
            model = TranslationProject

        def process_extra_fields(self):
            if self.instance.pk is not None:
                if self.cleaned_data.get('initialize', None):
                    self.instance.initialize()

                if (self.cleaned_data.get('update', None) or
                    not self.instance.stores.count()):
                    self.instance.update_against_templates()

    return TranslationProjectForm
