#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2014 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
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

        source_language = forms.ModelChoiceField(
            label=_('Source Language'),
            initial=default_lang.pk,
            queryset=queryset,
        )

        class Meta:
            model = Project

        def __init__(self, *args, **kwargs):
            super(ProjectForm, self).__init__(*args, **kwargs)
            if self.instance.id:
                has_stores = Store.objects.filter(
                    translation_project__project=self.instance
                ).count()

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
                raise ValidationError(_('"%s" cannot be used as a project '
                                        'code' % value))
            return value

    def generate_link(project):
        url = reverse('pootle-project-admin-languages', args=[project.code])
        return '<a href="%s">%s</a>' % (url, project.code)

    return util.edit(
            request,
            'admin/projects.html',
            Project,
            link=generate_link,
            form=ProjectForm,
            exclude=('report_email', ),
            can_delete=True,
    )
