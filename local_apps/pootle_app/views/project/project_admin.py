#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

from django.utils.translation import ugettext as _
from django import forms

from pootle_misc.baseurl import l

from pootle_app.models import Project, TranslationProject
from pootle_app import project_tree
from pootle_app.views.admin import util

@util.user_is_admin
def view(request, project_code):
    current_project = Project.objects.get(code=project_code)
    try:
        template_translation_project = TranslationProject.objects.get(project=current_project, language__code='templates')
    except TranslationProject.DoesNotExist:
        template_translation_project = None

    class TranslationProjectForm(forms.ModelForm):
        if template_translation_project is not None:
            update = forms.BooleanField(required=False, label=_("Update from templates"))
        #FIXME: maybe we can detect if initialize is needed to avoid
        # displaying it when not relevant
        initialize = forms.BooleanField(required=False, label=_("Initialize"))
        project = forms.ModelChoiceField(queryset=Project.objects.filter(pk=current_project.pk),
                                         initial=current_project.pk, widget=forms.HiddenInput)
        class Meta:
            prefix="existing_language"        

        def save(self, commit=True):
            if self.instance.pk is not None:
                if self.cleaned_data['initialize']:
                    self.instance.initialize()

                if self.cleaned_data['update']:
                    project_tree.convert_templates(template_translation_project, self.instance)
            super(TranslationProjectForm, self).save(commit)
            
            
    queryset = TranslationProject.objects.filter(project=current_project).order_by('pootle_path')
    
    model_args = {}
    model_args['project'] = { 'code': current_project.code,
                              'name': current_project.fullname }
    model_args['title'] = _("Project Admin: %s", current_project.fullname)
    model_args['formid'] = "translation-projects"
    model_args['submitname'] = "changetransprojects"
    link = lambda instance: '<a href="%s">%s</a>' % (l(instance.pootle_path + 'admin_permissions.html'), instance.language)
    return util.edit(request, 'project/project_admin.html', TranslationProject, model_args, link, linkfield="language",
                     queryset=queryset, can_delete=True, form=TranslationProjectForm)

