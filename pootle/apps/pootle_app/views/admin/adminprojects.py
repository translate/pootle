#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from pootle.core.decorators import admin_required
from pootle_app.views.admin import util
from pootle_language.models import Language
from pootle_project.models import Project, RESERVED_PROJECT_CODES
from pootle_store.models import Store


@admin_required
def view(request):
    queryset = Language.objects.exclude(code='templates')
    try:
        default_lang = Language.objects.get(code='en')
    except Language.DoesNotExist:
        default_lang = queryset[0]


    class ProjectForm(forms.ModelForm):
        class Meta:
            model = Project

        source_language = forms.ModelChoiceField(label=_('Source Language'),
                initial=default_lang.pk, queryset=queryset)

        def __init__(self, *args, **kwargs):
            super(ProjectForm, self).__init__(*args, **kwargs)
            if self.instance.id:
                has_stores = Store.objects.filter(
                        translation_project__project=self.instance
                    ).count
                if has_stores:
                    self.fields['localfiletype'].widget.attrs['disabled'] = True
                    self.fields['localfiletype'].required = False
                if (self.instance.treestyle != 'auto' and
                    self.instance.translationproject_set.count() and
                    self.instance.treestyle ==
                        self.instance._detect_treestyle()):
                    self.fields['treestyle'].widget.attrs['disabled'] = True
                    self.fields['treestyle'].required = False
            self.fields['checkstyle'].widget.attrs['class'] = \
                "js-select2 select2-checkstyle"
            self.fields['localfiletype'].widget.attrs['class'] = \
                "js-select2 select2-localfiletype"
            self.fields['treestyle'].widget.attrs['class'] = \
                "js-select2 select2-treestyle"
            self.fields['source_language'].widget.attrs['class'] = \
                "js-select2 select2-language"

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
                raise ValidationError(
                    _('"%s" cannot be used as a project code' % (value,))
                )
            return value

    return util.edit(
            request,
            'admin/admin_general_projects.html',
            Project,
            link='/projects/%s/admin.html',
            form=ProjectForm,
            exclude=('description', 'report_target'),
            can_delete=True,
    )
