#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

import logging
import os
from itertools import groupby

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _, ungettext

from pootle.core.decorators import (get_path_obj, get_resource_context,
                                    permission_required)
from pootle.core.helpers import get_filter_name, get_translation_context
from pootle.core.url_helpers import split_pootle_path
from pootle_app.models.permissions import check_permission
from pootle_app.models import Directory
from pootle_app.views.admin.permissions import admin_permissions as admin_perms
from pootle_misc.browser import get_children, get_table_headings
from pootle_misc.checks import get_quality_check_failures
from pootle_misc.stats import (get_raw_stats, get_translation_stats,
                               get_translate_actions)
from pootle_misc.util import jsonify, ajax_required
from pootle_statistics.models import Submission
from pootle_store.models import Store
from pootle_store.views import get_step_query


@get_path_obj
@permission_required('administrate')
def admin_permissions(request, translation_project):
    language = translation_project.language
    project = translation_project.project

    template_vars = {
        'translation_project': translation_project,
        "project": project,
        "language": language,
        "directory": translation_project.directory,
    }

    return admin_perms(request, translation_project.directory,
                       "translation_projects/admin/permissions.html",
                       template_vars)


@get_path_obj
@permission_required('administrate')
def rescan_files(request, translation_project):
    try:
        translation_project.scan_files()

        for store in translation_project.stores.exclude(file='').iterator():
            store.sync(update_translation=True)
            store.update(update_structure=True, update_translation=True)

        messages.success(request, _("Translation project files have been "
                                    "rescanned."))
    except Exception, e:
        logging.error(u"Error while rescanning translation project files: %s",
                      e)
        messages.error(request, _("Error while rescanning translation project "
                                  "files."))

    language = translation_project.language.code
    project = translation_project.project.code
    overview_url = reverse('pootle-tp-overview', args=[language, project, ''])

    return HttpResponseRedirect(overview_url)


@get_path_obj
@permission_required('administrate')
def update_against_templates(request, translation_project):
    try:
        translation_project.update_against_templates()

        messages.success(request, _("Translation project has been updated "
                                    "against latest templates."))
    except Exception, e:
        logging.error(u"Error while updating translation project against "
                      u"latest templates: %s", e)
        messages.error(request, _("Error while updating translation project "
                                  "against latest templates."))

    language = translation_project.language.code
    project = translation_project.project.code
    overview_url = reverse('pootle-tp-overview', args=[language, project, ''])

    return HttpResponseRedirect(overview_url)


@get_path_obj
@permission_required('administrate')
def delete_path_obj(request, translation_project, dir_path, filename=None):
    """Deletes the path objects under `dir_path` (+ `filename`) from the
    filesystem, including `dir_path` in case it's not a translation project."""
    current_path = translation_project.directory.pootle_path + dir_path

    try:
        if filename:
            current_path = current_path + filename
            store = get_object_or_404(Store, pootle_path=current_path)
            stores_to_delete = [store]
            directory = None
        else:
            directory = get_object_or_404(Directory, pootle_path=current_path)
            stores_to_delete = directory.stores

        # Delete stores in the current context from the DB and the filesystem
        for store in stores_to_delete:
            # First from the FS
            if store.file:
                store.file.storage.delete(store.file.name)

            # From the DB after
            store.delete()

        if directory:
            directory_is_tp = directory.is_translationproject()

            # First remove children directories from the DB
            for child_dir in directory.child_dirs.iterator():
                child_dir.delete()

            # Then the current directory (only if we are not in the root of the
            # translation project)
            if not directory_is_tp:
                directory.delete()

            # And finally all the directory tree from the filesystem (excluding
            # the root of the translation project)
            try:
                import shutil
                po_dir = unicode(settings.PODIRECTORY)
                root_dir = os.path.join(po_dir, directory.get_real_path())

                if directory_is_tp:
                    children = [os.path.join(root_dir, child) \
                                for child in os.listdir(root_dir)]
                    child_dirs = filter(os.path.isdir, children)
                    for child_dir in child_dirs:
                        shutil.rmtree(child_dir)
                else:
                    shutil.rmtree(root_dir)
            except OSError:
                messages.warning(request, _("Symbolic link hasn't been "
                                            "removed from the filesystem."))

        if directory:
            messages.success(request, _("Directory and its containing files "
                                        "have been deleted."))
        else:
            messages.success(request, _("File has been deleted."))
    except Exception, e:
        logging.error(u"Error while trying to delete %s: %s",
                      current_path, e)
        if directory:
            messages.error(request, _("Error while trying to delete "
                                      "directory."))
        else:
            messages.error(request, _("Error while trying to delete file."))

    language = translation_project.language.code
    project = translation_project.project.code
    overview_url = reverse('pootle-tp-overview', args=[language, project, ''])

    return HttpResponseRedirect(overview_url)


@get_path_obj
@permission_required('view')
@get_resource_context
def overview(request, translation_project, dir_path, filename=None):
    can_edit = check_permission('administrate', request)

    project = translation_project.project
    language = translation_project.language

    directory = request.directory
    store = request.store
    resource_obj = store or directory

    #checks_stats = resource_obj.getcompletestats()
    #translate_actions = get_translate_actions(resource_obj, path_stats, checks_stats)
    #TODO work via AJAX

    # Build URL for getting more summary information for the current path
    url_args = [language.code, project.code, resource_obj.path]
    url_path_summary_more = reverse('pootle-tp-summary', args=url_args)

    ctx = {
        'translation_project': translation_project,
        'project': project,
        'language': language,
        'resource_obj': resource_obj,
        'resource_path': request.resource_path,
        'can_edit': can_edit,
        'url_path_summary_more': url_path_summary_more,
    }

    if store is None:
        table_fields = ['name', 'progress', 'total', 'need-translation',
                        'suggestions', 'activity']
        ctx.update({
            'table': {
                'id': 'tp',
                'fields': table_fields,
                'headings': get_table_headings(table_fields),
                'items': get_children(translation_project, directory),
            }
        })

    return render_to_response("translation_projects/overview.html", ctx,
                              context_instance=RequestContext(request))

@get_path_obj
@permission_required('view')
@get_resource_context
def overview_stats(request, translation_project, dir_path, filename=None):
    directory = request.directory
    store = request.store
    resource_obj = store or directory

    stats = resource_obj.get_stats()

    return HttpResponse(jsonify(stats), mimetype="application/json")

@get_path_obj
@permission_required('view')
@get_resource_context
def translate(request, translation_project, dir_path, filename):
    language = translation_project.language
    project = translation_project.project

    is_terminology = (project.is_terminology or request.store and
                                                request.store.is_terminology)
    context = get_translation_context(request, is_terminology=is_terminology)
    context.update({
        'language': language,
        'project': project,
        'translation_project': translation_project,

        'editor_extends': 'translation_projects/base.html',
        'editor_body_id': 'tptranslate',
    })

    return render_to_response('editor/main.html', context,
                              context_instance=RequestContext(request))


@get_path_obj
@permission_required('view')
def export_view(request, translation_project, dir_path, filename=None):
    """Displays a list of units with filters applied."""
    current_path = translation_project.directory.pootle_path + dir_path

    if filename:
        current_path = current_path + filename
        store = get_object_or_404(Store, pootle_path=current_path)
        units_qs = store.units
    else:
        store = None
        units_qs = translation_project.units.filter(
            store__pootle_path__startswith=current_path,
        )

    filter_name, filter_extra = get_filter_name(request.GET)

    units = get_step_query(request, units_qs)
    unit_groups = [(path, list(units)) for path, units in
                   groupby(units, lambda x: x.store.path)]

    ctx = {
        'source_language': translation_project.project.source_language,
        'language': translation_project.language,
        'project': translation_project.project,
        'unit_groups': unit_groups,
        'filter_name': filter_name,
        'filter_extra': filter_extra,
    }

    return render_to_response('translation_projects/export_view.html', ctx,
                              context_instance=RequestContext(request))


#@ajax_required
@get_path_obj
def path_summary_more(request, translation_project, dir_path, filename=None):
    """Returns an HTML snippet with more detailed summary information
       for the current path."""
    current_path = translation_project.directory.pootle_path + dir_path

    if filename:
        current_path = current_path + filename
        store = get_object_or_404(Store, pootle_path=current_path)
        directory = store.parent
    else:
        directory = get_object_or_404(Directory, pootle_path=current_path)
        store = None

    path_obj = store or directory

    path_stats = get_raw_stats(path_obj)
    translation_stats = get_translation_stats(path_obj, path_stats)
    quality_checks = get_quality_check_failures(path_obj, path_stats)

    context = {
        'check_failures': quality_checks,
        'trans_stats': translation_stats,
    }

    return render_to_response('translation_projects/xhr_path_summary.html',
                              context, RequestContext(request))


@ajax_required
@get_path_obj
@permission_required('administrate')
def edit_settings(request, translation_project):
    from pootle_translationproject.forms import DescriptionForm
    form = DescriptionForm(request.POST, instance=translation_project)

    response = {}
    rcode = 400

    if form.is_valid():
        form.save()
        rcode = 200

        if translation_project.description:
            the_html = translation_project.description
        else:
            the_html = u"".join([
                u'<p class="placeholder muted">',
                _(u"No description yet."),
                u"</p>"
            ])

        response["description"] = the_html

    path_args = split_pootle_path(translation_project.pootle_path)[:2]
    action_url = reverse('pootle-tp-admin-settings', args=path_args)
    context = {
        "form": form,
        "form_action": action_url,
    }
    t = loader.get_template('admin/_settings_form.html')
    c = RequestContext(request, context)
    response['form'] = t.render(c)

    return HttpResponse(jsonify(response), status=rcode,
                        mimetype="application/json")
