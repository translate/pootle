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
from django.forms.models import modelformset_factory

from pootle_app.views               import indexpage, pagelayout
from pootle_app.lib.util            import redirect
from pootle_app.models              import Language, Project, TranslationProject
from pootle_app                     import project_tree
from pootle_app.views.util          import render_to_kid, render_jtoolkit, \
    KidRequestContext, init_formset_from_data, choices_from_models, selected_model

class LanguageForm(forms.ModelForm):
    update = forms.BooleanField(required=False)

    class Meta:
        prefix="existing_language"        

LanguageFormset = modelformset_factory(Language, LanguageForm, fields=['update'], extra=0)

def user_can_admin_project(f):
    def decorated_f(request, project_code, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('/projects/%s' % project_code, message=_("Only administrators may modify the project options."))
        else:
            return f(request, project_code, *args, **kwargs)
    return decorated_f

@user_can_admin_project
def view(request, project_code):
    project = Project.objects.get(code=project_code)
    process_get(request, project)
    process_post(request, project)

    existing_languages = [translation_project.language for translation_project
                          in TranslationProject.objects.filter(project=project).exclude(language__code='templates')]
    formset = LanguageFormset(queryset=existing_languages)
    new_language_form = make_new_language_form(existing_languages)
    has_template = TranslationProject.objects.filter(project=project, language__code='templates').count() > 0

    template_vars = {
        "pagetitle":          _("Pootle Admin: %s") % project.fullname,
        "norights_text":      _("You do not have the rights to administer this project."),
        "project":            project,
        "iso_code":           _("ISO Code"),
        "full_name":          _("Full Name"),
        "existing_title":     _("Existing languages"),
        "formset":            formset,
        "new_language_form":  new_language_form,
        "update_button":      _("Update Languages"),
        "add_button":         _("Add Language"),
        "main_link":          _("Back to main page"),
        "update_link":        _("Update from templates"), 
        "initialize_link":    _("Initialize"),
        "instancetitle":      pagelayout.get_title(),
        "has_template":       has_template
        }

    return render_to_kid("project/projectadmin.html", KidRequestContext(request, template_vars))


def make_new_language_form(existing_languages, post_vars=None):
    new_languages = [language for language in Language.objects.all() if not language in set(existing_languages)]

    class NewLanguageForm(forms.Form):
        add_language = forms.ChoiceField(choices=choices_from_models(new_languages), label=_("Add language"))

    return NewLanguageForm(post_vars)


def process_get(request, project):
    if request.method == 'GET':
        #try:
        language_code = request.GET['updatelanguage']
        translation_project = TranslationProject.objects.get(language__code=language_code, project=project)
        template_translation_project = TranslationProject.objects.get(language__code='templates',
                                                                      project=translation_project.project_id)
        if 'initialize' in request.GET:
            translation_project.initialize()
        elif 'doupdatelanguage' in request.GET:
            project_tree.convert_templates(template_translation_project, translation_project)
        #except KeyError:
        #    pass


def process_post(request, project):
    def process_existing_languages(request, project):
        formset = init_formset_from_data(LanguageFormset, request.POST)
        if formset.is_valid():
            for form in formset.forms:
                if form['update'].data:
                    template_translation_project = TranslationProject.objects.get(language__code='templates',
                                                                                  project=project)
                    language = form.instance
                    translation_project = TranslationProject.objects.get(language=language, project=project)
                    project_tree.convert_templates(template_translation_project, translation_project)
        return formset

    def process_new_language(request, project, languages):
        new_language_form = make_new_language_form(languages, request.POST)

        if new_language_form.is_valid():
            new_language = selected_model(Language, new_language_form['add_language'])
            if new_language is not None:
                # This will create the necessary directory for our TranslationProject
                project_tree.ensure_translation_project_dir(new_language, project)
                translation_project = TranslationProject(language=new_language, project=project)
                translation_project.save()

    if request.method == 'POST':
        formset = process_existing_languages(request, project)
        process_new_language(request, project, [form.instance for form in formset.forms])

