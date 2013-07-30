#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
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

from django import forms
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _, ungettext

from pootle.i18n.gettext import tr_lang
from pootle_app.models import Directory
from pootle_app.models.permissions import (get_matching_permissions,
                                           check_permission)
from pootle_app.views.admin import util
from pootle_app.views.admin.permissions import admin_permissions
from pootle_app.views.index.index import getprojects
from pootle_app.views.top_stats import gentopstats_project, gentopstats_root
from pootle_language.models import Language
from pootle_misc import dispatch
from pootle_misc.baseurl import l
from pootle_misc.browser import get_table_headings
from pootle_misc.forms import LiberalModelChoiceField
from pootle_misc.stats import get_raw_stats, stats_descriptions
from pootle_misc.util import ajax_required, jsonify
from pootle_profile.models import get_profile
from pootle_project.models import Project
from pootle_statistics.models import Submission
from pootle_translationproject.models import TranslationProject


def get_last_action(translation_project):
    try:
        return Submission.objects.filter(
            translation_project=translation_project).latest().as_html()
    except Submission.DoesNotExist:
        return ''


def make_language_item(request, translation_project):
    href = '/%s/%s/' % (translation_project.language.code,
                        translation_project.project.code)
    href_all = dispatch.translate(translation_project)
    href_todo = dispatch.translate(translation_project, state='incomplete')

    project_stats = get_raw_stats(translation_project)

    tooltip_dict = {
        'percentage': project_stats['translated']['percentage']
    }

    info = {
        'code': translation_project.language.code,
        'href': href,
        'href_all': href_all,
        'href_todo': href_todo,
        'title': tr_lang(translation_project.language.fullname),
        'stats': project_stats,
        'lastactivity': get_last_action(translation_project),
        'tooltip': _('%(percentage)d%% complete', tooltip_dict),
    }

    errors = project_stats.get('errors', 0)

    if errors:
        info['errortooltip'] = ungettext('Error reading %d file',
                                         'Error reading %d files', errors,
                                         errors)

    info.update(stats_descriptions(project_stats))

    return info


def get_project_base_template_vars(request, project, can_edit):
    """Get the base template vars for project overview view."""
    translation_projects = project.translationproject_set.all()

    items = [make_language_item(request, translation_project) \
            for translation_project in translation_projects.iterator()]
    items.sort(lambda x, y: locale.strcoll(x['title'], y['title']))

    languagecount = len(translation_projects)
    project_stats = get_raw_stats(project)

    summary_dict = {
        "languages": languagecount,
        "average": project_stats['translated']['percentage'],
    }

    summary = ungettext('%(languages)d language, %(average)d%% translated',
                        '%(languages)d languages, %(average)d%% translated',
                        languagecount, summary_dict)

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'activity']

    template_vars = {
        'project': {
            'code': project.code,
            'name': project.fullname,
            'description': project.description,
            'summary': summary,
        },
        'topstats': gentopstats_project(project),
        'can_edit': can_edit,
        'table': {
            'id': 'project',
            'proportional': False,
            'fields': table_fields,
            'headings': get_table_headings(table_fields),
            'items': items,
        },
    }

    return template_vars


def project_language_index(request, project_code):
    """Page listing all languages added to project."""
    project = get_object_or_404(Project, code=project_code)
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   project.directory)
    if not check_permission('view', request):
        raise PermissionDenied

    can_edit = check_permission('administrate', request)
    templatevars = get_project_base_template_vars(request, project, can_edit)

    if can_edit:
        from pootle_project.forms import DescriptionForm
        templatevars['form'] = DescriptionForm(instance=project)

    return render_to_response('project/project.html', templatevars,
                              context_instance=RequestContext(request))


@ajax_required
def project_settings_edit(request, project_code):
    project = get_object_or_404(Project, code=project_code)
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   project.directory)
    if not check_permission('administrate', request):
        raise PermissionDenied

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
                _(u"No description yet."),
                u"</p>",
            ])

        response["description"] = the_html

    context = {
        "form": form,
        "form_action": project.pootle_path + "edit_settings.html",
    }
    t = loader.get_template('admin/general_settings_form.html')
    c = RequestContext(request, context)
    response['form'] = t.render(c)

    return HttpResponse(jsonify(response), status=rcode,
                        mimetype="application/json")


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


def project_admin(request, project_code):
    """adding and deleting project languages"""
    current_project = Project.objects.get(code=project_code)
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   current_project.directory)

    if not check_permission('administrate', request):
        raise PermissionDenied(_("You do not have rights to administer this "
                                 "project."))

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

    link = lambda instance: '<a href="%s">%s</a>' % (
            l(instance.pootle_path + 'admin_permissions.html'),
            instance.language,
    )

    return util.edit(request, 'project/project_admin.html', TranslationProject,
                     model_args, link, linkfield="language", queryset=queryset,
                     can_delete=True, form=TranslationProjectForm,
                     formset=TranslationProjectFormSet,
                     exclude=('description',))


def project_admin_permissions(request, project_code):
    project = get_object_or_404(Project, code=project_code)
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   project.directory)

    if not check_permission('administrate', request):
        raise PermissionDenied(_("You do not have rights to administer this "
                                 "project."))

    template_vars = {
        "project": project,
        "directory": project.directory,
        "feed_path": project.pootle_path[1:],
    }

    return admin_permissions(request, project.directory,
                             "project/admin_permissions.html", template_vars)


def projects_index(request):
    """page listing all projects"""
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   Directory.objects.root)
    if not check_permission('view', request):
        raise PermissionDenied

    table_fields = ['project', 'progress', 'activity']

    templatevars = {
        'table': {
            'id': 'projects',
            'proportional': False,
            'fields': table_fields,
            'headings': get_table_headings(table_fields),
            'items': getprojects(request),
        },
        'topstats': gentopstats_root(),
    }

    return render_to_response('project/projects.html', templatevars,
                              RequestContext(request))
