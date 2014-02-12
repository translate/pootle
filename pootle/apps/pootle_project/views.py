#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

import locale

from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _, ungettext
from django.views.decorators.http import require_POST

from taggit.models import Tag

from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.helpers import get_translation_context
from pootle.core.url_helpers import split_pootle_path
from pootle.i18n.gettext import tr_lang
from pootle_app.models import Directory
from pootle_app.models.permissions import check_permission
from pootle_app.views.admin import util
from pootle_app.views.admin.permissions import admin_permissions
from pootle_app.views.index.index import getprojects
from pootle_app.views.top_stats import gentopstats_project, gentopstats_root
from pootle_misc.baseurl import l
from pootle_misc.browser import get_table_headings
from pootle_misc.util import ajax_required, jsonify
from pootle_profile.models import get_profile
from pootle_project.forms import (TranslationProjectFormSet,
                                  TranslationProjectTagForm, tp_form_factory)
from pootle_project.models import Project
from pootle_statistics.models import Submission
from pootle_tagging.models import Goal
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

    info = {
        'project': translation_project.project.code,
        'code': translation_project.code,
        'href': href,
        'href_all': href_all,
        'href_todo': href_todo,
        'title': tr_lang(translation_project.language.fullname),
        'lastactivity': get_last_action(translation_project),
        'tags': translation_project.tag_like_objects,
        'pk': translation_project.pk,
    }

    return info


def get_project_base_template_vars(request, project, can_edit):
    """Get the base template vars for project overview view."""
    translation_projects = project.translationproject_set.all()

    items = [make_language_item(translation_project) \
            for translation_project in translation_projects.iterator()]
    items.sort(lambda x, y: locale.strcoll(x['title'], y['title']))

    languagecount = len(translation_projects)

    summary = ungettext('%(languages)d language',
                        '%(languages)d languages',
                        languagecount, {"languages": languagecount})

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'activity', 'tags']

    template_vars = {
        'resource_obj': request.resource_obj,
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


@ajax_required
@get_path_obj
@permission_required('view')
def ajax_list_tags(request, project):
    from django.contrib.contenttypes.models import ContentType
    from django.core import serializers

    translation_projects = project.translationproject_set.all()
    ct = ContentType.objects.get_for_model(TranslationProject)
    criteria = {
        "taggit_taggeditem_items__content_type": ct,
        "taggit_taggeditem_items__object_id__in": translation_projects,
    }

    queryset = Tag.objects.filter(**criteria).distinct() #.values_list("id", "name")

    return HttpResponse(serializers.serialize("json", queryset))

@require_POST
@ajax_required
@get_path_obj
@permission_required('administrate')
def ajax_remove_tag_from_tp_in_project(request, translation_project, tag_name):

    if tag_name.startswith("goal:"):
        translation_project.goals.remove(tag_name)
    else:
        translation_project.tags.remove(tag_name)
    context = {
        'tp_tags': translation_project.tags.all().order_by('name'),
        'project': translation_project.project.code,
        'language': translation_project.language.code,
    }
    response = render_to_response('projects/xhr_tags_list.html',
                                  context, RequestContext(request))
    response.status_code = 201
    return response


def _add_tag(request, translation_project, tag_like_object):
    if isinstance(tag_like_object, Tag):
        translation_project.tags.add(tag_like_object)
    else:
        translation_project.goals.add(tag_like_object)
    context = {
        'tp_tags': translation_project.tag_like_objects,
        'project': translation_project.project.code,
        'language': translation_project.language.code,
    }
    response = render_to_response('projects/xhr_tags_list.html',
                                  context, RequestContext(request))
    response.status_code = 201
    return response


@require_POST
@ajax_required
@get_path_obj
@permission_required('administrate')
def ajax_add_tag_to_tp_in_project(request, project):
    """Return an HTML snippet with the failed form or blank if valid."""

    add_tag_form = TranslationProjectTagForm(request.POST, project=project)

    if add_tag_form.is_valid():
        translation_project = add_tag_form.cleaned_data['translation_project']
        new_tag_like_object = add_tag_form.save()
        return _add_tag(request, translation_project, new_tag_like_object)
    else:
        # If the form is invalid, perhaps it is because the tag already
        # exists, so instead of creating the tag just retrieve it and add
        # it to the translation project.
        try:
            # Try to retrieve the translation project.
            kwargs = {
                'pk': add_tag_form.data['translation_project'],
            }
            translation_project = TranslationProject.objects.get(**kwargs)

            # Check if the tag (or goal) is already added to the translation
            # project, or try adding it.
            criteria = {
                'name': add_tag_form.data['name'],
                'slug': add_tag_form.data['slug'],
            }
            if len(translation_project.tags.filter(**criteria)) == 1:
                # If the tag is already applied to the translation project then
                # avoid reloading the page.
                return HttpResponse(status=204)
            elif len(translation_project.goals.filter(**criteria)) == 1:
                # If the goal is already applied to the translation project
                # then avoid reloading the page.
                return HttpResponse(status=204)
            else:
                # Else add the tag (or goal) to the translation project.
                if criteria['name'].startswith("goal:"):
                    tag_like_object = Goal.objects.get(**criteria)
                else:
                    tag_like_object = Tag.objects.get(**criteria)
                return _add_tag(request, translation_project, tag_like_object)
        except Exception:
            # If the form is invalid and the tag (or goal) doesn't exist yet
            # then display the form with the error messages.
            url_kwargs = {
                'project_code': project.code,
            }
            context = {
                'add_tag_form': add_tag_form,
                'add_tag_action_url': reverse('pootle-xhr-tag-tp-in-project',
                                              kwargs=url_kwargs)
            }
            return render_to_response('core/xhr_add_tag_form.html',
                                      context, RequestContext(request))



@get_path_obj
@permission_required('view')
def overview(request, project):
    """Page listing all languages added to project."""
    can_edit = check_permission('administrate', request)
    templatevars = get_project_base_template_vars(request, project, can_edit)

    if can_edit:
        from pootle_project.forms import DescriptionForm
        url_kwargs = {
            'project_code': project.code,
        }
        templatevars.update({
            'form': DescriptionForm(instance=project),
            'add_tag_form': TranslationProjectTagForm(project=project),
            'add_tag_action_url': reverse('pootle-xhr-tag-tp-in-project',
                                          kwargs=url_kwargs),
        })

    return render_to_response('projects/overview.html', templatevars,
                              context_instance=RequestContext(request))


@require_POST
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
                _(u"No description yet."),
                u"</p>",
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


@get_path_obj
@permission_required('administrate')
def project_admin(request, current_project):
    """Adding and deleting project languages."""

    tp_form_class = tp_form_factory(current_project)

    queryset = TranslationProject.objects.filter(project=current_project) \
                                         .order_by('pootle_path')

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
                     can_delete=True, form=tp_form_class,
                     formset=TranslationProjectFormSet,
                     exclude=('description',))


@get_path_obj
@permission_required('administrate')
def project_admin_permissions(request, project):
    template_vars = {
        "project": project,
        "directory": project.directory,
        "feed_path": project.pootle_path[1:],
    }
    return admin_permissions(request, project.directory,
                             "projects/admin/permissions.html", template_vars)


@get_path_obj
@permission_required('view')
def projects_index(request, root):
    """page listing all projects"""
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

    return render_to_response('projects/list.html', templatevars,
                              RequestContext(request))
