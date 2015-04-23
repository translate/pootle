#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.utils.translation import ugettext as _

from pootle_language.models import Language
from pootle_misc.forms import LiberalModelChoiceField
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


def tp_form_factory(current_project):

    class TranslationProjectForm(forms.ModelForm):

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
            fields = ('language', 'project')

    return TranslationProjectForm
