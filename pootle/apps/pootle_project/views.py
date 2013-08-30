#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _, ungettext

from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.helpers import get_translation_context
from pootle.core.url_helpers import split_pootle_path
from pootle.i18n.gettext import tr_lang
from pootle_app.models.permissions import check_permission
from pootle_app.views.admin import util
from pootle_app.views.admin.permissions import admin_permissions
from pootle_app.views.index.index import getprojects
from pootle_app.views.top_stats import gentopstats_project, gentopstats_root
from pootle_language.models import Language
from pootle_misc.baseurl import l
from pootle_misc.browser import get_table_headings
from pootle_misc.forms import LiberalModelChoiceField
from pootle_misc.stats import get_raw_stats, stats_descriptions
from pootle_misc.util import ajax_required, jsonify
from pootle_project.models import Project
from pootle_statistics.models import Submission
from pootle_translationproject.models import TranslationProject


def get_last_action(translation_project):
    try:
        return Submission.objects.filter(
            translation_project=translation_project).latest().as_html()
    except Submission.DoesNotExist:
        return ''


def make_language_item(translation_project):
    href = translation_project.get_absolute_url()
    href_all = translation_project.get_translate_url()
    href_todo = translation_project.get_translate_url(state='incomplete')
    href_sugg = translation_project.get_translate_url(state='suggestions')

    project_stats = get_raw_stats(translation_project, include_suggestions=True)

    info = {
        'code': translation_project.language.code,
        'href': href,
        'href_all': href_all,
        'href_todo': href_todo,
        'href_sugg': href_sugg,
        'title': tr_lang(translation_project.language.fullname),
        'stats': project_stats,
        'lastactivity': get_last_action(translation_project),
        'tooltip': _('%(percentage)d%% complete',
                     {'percentage': project_stats['translated']['percentage']}),
    }

    errors = project_stats.get('errors', 0)

    if errors:
        info['errortooltip'] = ungettext('Error reading %d file', 'Error reading %d files', errors, errors)

    info.update(stats_descriptions(project_stats))

    return info


@get_path_obj
@permission_required('view')
def overview(request, project):
    """page listing all languages added to project"""
    can_edit = check_permission('administrate', request)

    translation_projects = project.translationproject_set.all()

    items = [make_language_item(translation_project)
             for translation_project in translation_projects.iterator()]
    items.sort(lambda x, y: locale.strcoll(x['title'], y['title']))

    languagecount = len(translation_projects)
    project_stats = get_raw_stats(project)
    translated = project_stats['translated']['percentage']

    topstats = gentopstats_project(project)

    table_fields = ['name', 'progress', 'total', 'need-translation', 'suggestions', 'activity']
    table = {
        'id': 'project',
        'proportional': False,
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': items,
    }

    templatevars = {
        'project': {
          'code': project.code,
          'name': project.fullname,
          'description': project.description,
          'summary': ungettext('%(languages)d language, %(translated)d%% translated',
                               '%(languages)d languages, %(translated)d%% translated',
                               languagecount, {"languages": languagecount,
                                               "translated": translated}),
        },
        'topstats': topstats,
        'stats': project_stats,
        'can_edit': can_edit,
        'table': table,
    }

    if can_edit:
        from pootle_project.forms import DescriptionForm
        templatevars['form'] = DescriptionForm(instance=project)

    return render_to_response('projects/overview.html', templatevars,
                              context_instance=RequestContext(request))


@ajax_required
@get_path_obj
@permission_required('administrate')
def project_settings_edit(request, project):
    from pootle_project.forms import DescriptionForm
    form = DescriptionForm(request.POST, instance=project)

    response = {}
    rcode = 400

    if form.is_valid():
        form.save()
        rcode = 200

        if project.description:
            the_html = project.description
        else:
            the_html = u"".join([
                u'<p class="placeholder muted">',
                _(u"No description yet."), u"</p>"
            ])

        response["description"] = the_html

    action_url = reverse('pootle-project-admin-settings', args=[project.code])
    context = {
        "form": form,
        "form_action": action_url,
    }
    t = loader.get_template('admin/_settings_form.html')
    c = RequestContext(request, context)
    response['form'] = t.render(c)

    return HttpResponse(jsonify(response), status=rcode,
                        mimetype="application/json")


@get_path_obj
@permission_required('view')
def translate(request, project):
    request.pootle_path = project.pootle_path
    # TODO: support arbitrary resources
    request.ctx_path = project.pootle_path
    request.resource_path = ''

    request.store = None
    request.directory = project.directory

    language = None

    context = get_translation_context(request)
    context.update({
        'language': language,
        'project': project,

        'editor_extends': 'projects/base.html',
        'editor_body_id': 'projecttranslate',
    })

    return render_to_response('editor/main.html', context,
                              context_instance=RequestContext(request))


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


@get_path_obj
@permission_required('administrate')
def project_admin(request, current_project):
    """adding and deleting project languages"""
    template_translation_project = current_project \
                                        .get_template_translationproject()


    class TranslationProjectForm(forms.ModelForm):

        if template_translation_project is not None:
            update = forms.BooleanField(required=False,
                                        label=_("Update against templates"))

        #FIXME: maybe we can detect if initialize is needed to avoid
        # displaying it when not relevant
        #initialize = forms.BooleanField(required=False, label=_("Initialize"))

        project = forms.ModelChoiceField(
                queryset=Project.objects.filter(pk=current_project.pk),
                initial=current_project.pk, widget=forms.HiddenInput
        )
        language = LiberalModelChoiceField(
                label=_("Language"),
                queryset=Language.objects.exclude(
                    translationproject__project=current_project),
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

    queryset = TranslationProject.objects.filter(
            project=current_project).order_by('pootle_path')

    model_args = {
        'project': {
            'code': current_project.code,
            'name': current_project.fullname,
        }
    }

    def generate_link(tp):
        path_args = split_pootle_path(tp.pootle_path)[:2]
        perms_url = reverse('pootle-tp-admin-permissions', args=path_args)
        return '<a href="%s">%s</a>' % (perms_url, tp.language)

    return util.edit(request, 'projects/admin/languages.html',
                     TranslationProject, model_args, generate_link,
                     linkfield="language", queryset=queryset,
                     can_delete=True, form=TranslationProjectForm,
                     formset=TranslationProjectFormSet,
                     exclude=('description',))


@get_path_obj
@permission_required('administrate')
def project_admin_permissions(request, project):
    template_vars = {
        "project": project,
        "directory": project.directory,
    }

    return admin_permissions(request, project.directory,
                             "projects/admin/permissions.html", template_vars)


@get_path_obj
@permission_required('view')
def projects_index(request, root):
    """page listing all projects"""
    table_fields = ['project', 'progress', 'activity']
    table = {
        'id': 'projects',
        'proportional': False,
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': getprojects(request),
    }

    templatevars = {
        'table': table,
        'topstats': gentopstats_root(),
    }

    return render_to_response('projects/list.html', templatevars,
                              RequestContext(request))
