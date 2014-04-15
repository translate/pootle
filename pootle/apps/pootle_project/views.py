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

from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from taggit.models import Tag

from pootle.core.browser import (get_table_headings, make_language_item,
                                 make_project_list_item)
from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.helpers import (get_export_view_context, get_overview_context,
                                 get_translation_context)
from pootle.core.url_helpers import split_pootle_path
from pootle_app.models.permissions import check_permission
from pootle_misc.util import ajax_required, jsonify
from pootle_project.forms import (TranslationProjectFormSet,
                                  TranslationProjectTagForm, tp_form_factory)
from pootle_project.models import Project
from pootle_tagging.models import Goal
from pootle_translationproject.models import TranslationProject


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

    queryset = Tag.objects.filter(**criteria).distinct()  # .values_list("id", "name")

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
    ctx = {
        'tp_tags': translation_project.tags.all().order_by('name'),
        'project': translation_project.project.code,
        'language': translation_project.language.code,
    }
    response = render(request, "projects/xhr_tags_list.html", ctx)
    response.status_code = 201
    return response


def _add_tag(request, translation_project, tag_like_object):
    if isinstance(tag_like_object, Tag):
        translation_project.tags.add(tag_like_object)
    else:
        translation_project.goals.add(tag_like_object)
    ctx = {
        'tp_tags': translation_project.tag_like_objects,
        'project': translation_project.project.code,
        'language': translation_project.language.code,
    }
    response = render(request, "projects/xhr_tags_list.html", ctx)
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
            ctx = {
                'add_tag_form': add_tag_form,
                'add_tag_action_url': reverse('pootle-xhr-tag-tp-in-project',
                                              kwargs=url_kwargs)
            }
            return render(request, "core/xhr_add_tag_form.html", ctx)


@get_path_obj
@permission_required('view')
def overview(request, project):
    """Page listing all languages added to project."""
    from locale import strcoll

    translation_projects = project.translationproject_set.all()

    items = [make_language_item(translation_project)
             for translation_project in translation_projects.iterator()]
    items.sort(lambda x, y: strcoll(x['title'], y['title']))

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'suggestions', 'critical', 'activity']

    ctx = get_overview_context(request)
    ctx.update({
        'project': {
            'code': project.code,
            'name': project.fullname,
            'description': project.description,
        },
        'can_edit': check_permission("administrate", request),
        'table': {
            'id': 'project',
            'proportional': False,
            'fields': table_fields,
            'headings': get_table_headings(table_fields),
            'items': items,
        },

        'browser_extends': 'projects/base.html',
        'browser_body_id': 'projectoverview',
    })

    if ctx['can_edit']:
        from pootle_project.forms import DescriptionForm
        tag_action_url = reverse('pootle-xhr-tag-tp-in-project',
                                 kwargs={'project_code': project.code})
        ctx.update({
            'form': DescriptionForm(instance=project),
            'form_action': reverse('pootle-project-admin-settings',
                                   args=[project.code]),
            'add_tag_form': TranslationProjectTagForm(project=project),
            'add_tag_action_url': tag_action_url,
        })

    return render(request, 'browser/overview.html', ctx)


@require_POST
@ajax_required
@get_path_obj
@permission_required('administrate')
def project_settings_edit(request, project):
    from pootle_project.forms import DescriptionForm
    form = DescriptionForm(request.POST, instance=project)

    response = {}
    status = 400

    if form.is_valid():
        form.save()
        status = 200

        if project.description:
            the_html = project.description
        else:
            the_html = u"".join([
                u'<p class="placeholder muted">',
                _(u"No description yet."),
                u"</p>",
            ])

        response["description"] = the_html

    ctx = {
        "form": form,
        "form_action": reverse('pootle-project-admin-settings',
                               args=[project.code]),
    }

    template = loader.get_template('admin/_settings_form.html')
    response['form'] = template.render(RequestContext(request, ctx))

    return HttpResponse(jsonify(response), status=status,
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

    ctx = get_translation_context(request)
    ctx.update({
        'language': None,
        'project': project,

        'editor_extends': 'projects/base.html',
        'editor_body_id': 'projecttranslate',
    })

    return render(request, "editor/main.html", ctx)


@get_path_obj
@permission_required('view')
def export_view(request, project):
    request.pootle_path = project.pootle_path
    # TODO: support arbitrary resources
    request.ctx_path = project.pootle_path
    request.resource_path = ''

    request.store = None
    request.directory = project.directory

    language = None

    ctx = get_export_view_context(request)
    ctx.update({
        'source_language': 'en',
        'language': language,
        'project': project,
    })

    return render_to_response('editor/export_view.html', ctx,
                              context_instance=RequestContext(request))


@get_path_obj
@permission_required('administrate')
def project_admin(request, project):
    """Adding and deleting project languages."""
    from pootle_app.views.admin.util import edit as admin_edit

    def generate_link(tp):
        path_args = split_pootle_path(tp.pootle_path)[:2]
        perms_url = reverse('pootle-tp-admin-permissions', args=path_args)
        return '<a href="%s">%s</a>' % (perms_url, tp.language)

    queryset = TranslationProject.objects.filter(project=project)
    queryset = queryset.order_by('pootle_path')

    model_args = {
        'project': {
            'code': project.code,
            'name': project.fullname,
        }
    }

    return admin_edit(request, 'projects/admin/languages.html',
                      TranslationProject, model_args, generate_link,
                      linkfield="language", queryset=queryset,
                      can_delete=True, form=tp_form_factory(project),
                      formset=TranslationProjectFormSet,
                      exclude=('description',))


@get_path_obj
@permission_required('administrate')
def project_admin_permissions(request, project):
    from pootle_app.views.admin.permissions import admin_permissions

    ctx = {
        "project": project,
        "directory": project.directory,
        "feed_path": project.pootle_path[1:],
    }
    return admin_permissions(request, project.directory,
                             "projects/admin/permissions.html", ctx)


@get_path_obj
@permission_required('view')
def projects_index(request, root):
    """Page listing all projects."""
    user_accessible_projects = Project.accessible_by_user(request.user)
    user_projects = Project.objects.filter(code__in=user_accessible_projects)
    items = [make_project_list_item(project) for project in user_projects]

    table_fields = ['name']

    ctx = {
        'table': {
            'id': 'projects',
            'fields': table_fields,
            'headings': get_table_headings(table_fields),
            'items': items,
        },
    }

    return render(request, "projects/list.html", ctx)
