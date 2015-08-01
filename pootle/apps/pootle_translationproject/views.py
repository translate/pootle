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

import logging
import os
import StringIO
from itertools import groupby

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from taggit.models import Tag

from pootle.core.decorators import (get_path_obj, get_resource_context,
                                    permission_required)
from pootle.core.helpers import get_filter_name, get_translation_context
from pootle.scripts.actions import (EXTDIR, StoreAction,
                                    TranslationProjectAction)
from pootle_app.models.permissions import check_permission
from pootle_app.models.signals import post_file_upload
from pootle_app.models import Directory
from pootle_app.project_tree import (ensure_target_dir_exists,
                                     direct_language_match_filename)
from pootle_app.views.admin.permissions import admin_permissions as admin_perms
from pootle_app.views.top_stats import gentopstats_translation_project
from pootle_misc.baseurl import redirect
from pootle_misc.browser import (get_children, get_goal_children,
                                 get_table_headings, make_goal_item)
from pootle_misc.checks import get_quality_check_failures
from pootle_misc.stats import (get_raw_stats, get_translation_stats,
                               get_path_summary)
from pootle_misc.util import jsonify, ajax_required
from pootle_profile.models import get_profile
from pootle_statistics.models import Submission, SubmissionTypes
from pootle_store.models import Store
from pootle_store.util import (absolute_real_path, relative_real_path,
                               add_trailing_slash)
from pootle_store.filetypes import factory_classes
from pootle_store.views import get_step_query
from pootle_tagging.decorators import get_goal
from pootle_tagging.forms import GoalForm, TagForm
from pootle_tagging.models import Goal

from .actions import action_groups
from .forms import DescriptionForm, upload_form_factory


@get_path_obj
@permission_required('administrate')
def admin_permissions(request, translation_project):
    template_vars = {
        'translation_project': translation_project,
        "project": translation_project.project,
        "language": translation_project.language,
        "directory": translation_project.directory,
        "feed_path": translation_project.pootle_path[1:],
    }
    return admin_perms(request, translation_project.directory,
                       "translation_project/admin_permissions.html",
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
    except Exception:
        logging.exception(u"Error while rescanning translation project files")
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
    except Exception:
        logging.exception(u"Error while updating translation project against "
                          u"latest templates")
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
    filesystem, including `dir_path` in case it's not a translation project.
    """
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

        # Delete stores in the current context from the DB and the filesystem.
        for store in stores_to_delete:
            # First from the FS.
            if store.file:
                store.file.storage.delete(store.file.name)

            # From the DB after.
            store.delete()

        if directory:
            directory_is_tp = directory.is_translationproject()

            # First remove children directories from the DB.
            for child_dir in directory.child_dirs.iterator():
                child_dir.delete()

            # Then the current directory (only if we are not in the root of the
            # translation project).
            if not directory_is_tp:
                directory.delete()

            # And finally all the directory tree from the filesystem (excluding
            # the root of the translation project).
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
    except Exception:
        logging.exception(u"Error while trying to delete %s", current_path)
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
@permission_required('commit')
def vcs_commit(request, translation_project, dir_path, filename):
    current_path = translation_project.directory.pootle_path + dir_path

    if filename:
        current_path = current_path + filename
        obj = get_object_or_404(Store, pootle_path=current_path)
        result = translation_project.commit_file(request.user, obj, request)
    else:
        obj = get_object_or_404(Directory, pootle_path=current_path)
        result = translation_project.commit_dir(request.user, obj, request)

    return redirect(obj.get_absolute_url())


@get_path_obj
@permission_required('commit')
def vcs_update(request, translation_project, dir_path, filename):
    current_path = translation_project.directory.pootle_path + dir_path

    if filename:
        current_path = current_path + filename
        obj = get_object_or_404(Store, pootle_path=current_path)
        result = translation_project.update_file(request, obj)
    else:
        obj = get_object_or_404(Directory, pootle_path=current_path)
        result = translation_project.update_dir(request, obj)

    return redirect(obj.get_absolute_url())


def _handle_upload_form(request, current_path, translation_project, directory):
    """Process the upload form in TP overview."""
    upload_form_class = upload_form_factory(request, current_path)

    if request.method == 'POST' and 'file' in request.FILES:
        upload_form = upload_form_class(request.POST, request.FILES)

        if not upload_form.is_valid():
            return upload_form
        else:
            django_file = upload_form.cleaned_data['file']
            overwrite = upload_form.cleaned_data['overwrite']
            upload_to = upload_form.cleaned_data['upload_to']
            upload_to_dir = upload_form.cleaned_data['upload_to_dir']

            # XXX Why do we scan here?
            translation_project.scan_files(vcs_sync=False)
            oldstats = translation_project.getquickstats()

            # The URL relative to the URL of the translation project. Thus, if
            # directory.pootle_path == /af/pootle/foo/bar, then
            # relative_root_dir == foo/bar.
            if django_file.name.endswith('.zip'):
                archive = True
                target_directory = upload_to_dir or directory
                upload_archive(request, target_directory, django_file,
                               overwrite)
            else:
                archive = False
                upload_file(request, directory, django_file, overwrite,
                            store=upload_to)

            translation_project.scan_files(vcs_sync=False)
            newstats = translation_project.getquickstats()

            # Create a submission. Doesn't fix stats but at least shows up in
            # last activity column.
            from django.utils import timezone
            s = Submission(
                creation_time=timezone.now(),
                translation_project=translation_project,
                submitter=get_profile(request.user),
                type=SubmissionTypes.UPLOAD,
                # The other fields are only relevant to unit-based changes.
            )
            s.save()

            post_file_upload.send(sender=translation_project,
                                  user=request.user, oldstats=oldstats,
                                  newstats=newstats, archive=archive)

    # Always return a blank upload form unless the upload form is not valid.
    return upload_form_class()


def goals_overview(*args, **kwargs):
    kwargs['in_goal_overview'] = True
    return overview(*args, **kwargs)


@get_path_obj
@permission_required('view')
@get_resource_context
@get_goal
def overview(request, translation_project, dir_path, filename=None,
             goal=None, in_goal_overview=False):
    current_path = translation_project.directory.pootle_path + dir_path

    if filename:
        current_path = current_path + filename
        store = get_object_or_404(Store, pootle_path=current_path)
        directory = store.parent
        template_vars = {
            'store_tags': store.tag_like_objects,
        }
        template = "translation_project/store_overview.html"
    else:
        store = None
        directory = get_object_or_404(Directory, pootle_path=current_path)
        template_vars = {
            'tp_tags': translation_project.tag_like_objects,
        }
        template = "translation_project/overview.html"

    if (check_permission('translate', request) or
        check_permission('suggest', request) or
        check_permission('overwrite', request)):

        template_vars.update({
            'upload_form': _handle_upload_form(request, current_path,
                                               translation_project, directory),
        })

    can_edit = check_permission('administrate', request)

    project = translation_project.project
    language = translation_project.language

    path_obj = store or directory

    latest_action = ''
    # If current directory is the TP root directory.
    if not directory.path:
        latest_action = translation_project.get_latest_submission()
    elif store is None:  # If this is not a file.
        latest_action = Submission.get_latest_for_dir(path_obj)

    path_stats = get_raw_stats(path_obj, include_suggestions=True)
    path_summary = get_path_summary(path_obj, path_stats, latest_action)

    #TODO enable again some actions when drilling down a goal.
    if goal is None:
        actions = action_groups(request, path_obj, path_stats=path_stats)
    else:
        actions = []

    action_output = ''
    running = request.GET.get(EXTDIR, '')

    #TODO enable the following again when drilling down a goal.
    if running and goal is None:
        if store:
            act = StoreAction
        else:
            act = TranslationProjectAction
        try:
            action = act.lookup(running)
        except KeyError:
            messages.error(request, _("Unable to find '%(action)s' in '%(extdir)s'") %
                                      {'action': act, 'extdir': running})
        else:
            if not getattr(action, 'nosync', False):
                (store or translation_project).sync()
            if action.is_active(request):
                vcs_dir = settings.VCS_DIRECTORY
                po_dir = settings.PODIRECTORY
                tp_dir = directory.get_real_path()
                store_fn = '*'
                if store:
                    tp_dir_slash = add_trailing_slash(tp_dir)
                    if store.file.name.startswith(tp_dir_slash):
                        # Note: store_f used below in reverse() call.
                        store_f = store.file.name[len(tp_dir_slash):]
                        store_fn = store_f.replace('/', os.sep)

                # Clear possibly stale output/error (even from other path_obj).
                action.set_output('')
                action.set_error('')
                try:
                    action.run(path=path_obj, root=po_dir, tpdir=tp_dir,
                               project=project.code, language=language.code,
                               store=store_fn,
                               style=translation_project.file_style,
                               vc_root=vcs_dir)
                except StandardError:
                    err = (_("Error while running '%s' extension action") %
                           action.title)
                    logging.exception(err)
                    if (action.error):
                        messages.error(request, action.error)
                    else:
                        messages.error(request, err)
                else:
                    if (action.error):
                        messages.warning(request, action.error)

                action_output = action.output
                if getattr(action, 'get_download', None):
                    export_path = action.get_download(path_obj)
                    if export_path:
                        import mimetypes
                        abs_path = absolute_real_path(export_path)
                        filename = os.path.basename(export_path)
                        mimetype, encoding = mimetypes.guess_type(filename)
                        mimetype = mimetype or 'application/octet-stream'
                        with open(abs_path, 'rb') as f:
                            response = HttpResponse(f.read(),
                                                    mimetype=mimetype)
                        response['Content-Disposition'] = (
                                'attachment; filename="%s"' % filename)
                        return response

                if not action_output:
                    if not store:
                        rev_args = [language.code, project.code, '']
                        overview_url = reverse('pootle-tp-overview',
                                               args=rev_args)
                    else:
                        slash = store_f.rfind('/')
                        store_d = ''
                        if slash > 0:
                            store_d = store_f[:slash]
                            store_f = store_f[slash + 1:]
                        elif slash == 0:
                            store_f = store_f[1:]
                        rev_args = [language.code, project.code, store_d,
                                    store_f]
                        overview_url = reverse('pootle-tp-overview',
                                               args=rev_args)
                    return HttpResponseRedirect(overview_url)

    if goal is None:
        description = translation_project.description
    else:
        description = goal.description

    template_vars.update({
        'translation_project': translation_project,
        'description': description,
        'project': project,
        'language': language,
        'path_obj': path_obj,
        'resource_path': request.resource_path,
        'path_summary': path_summary,
        'stats': path_stats,
        'topstats': gentopstats_translation_project(translation_project),
        'feed_path': directory.pootle_path[1:],
        'action_groups': actions,
        'action_output': action_output,
        'can_edit': can_edit,
    })

    tp_pootle_path = translation_project.pootle_path

    if store is None:
        path_obj_goals = Goal.get_goals_for_path(path_obj.pootle_path)
        path_obj_has_goals = len(path_obj_goals) > 0

        if in_goal_overview and path_obj_has_goals:
            # Then show the goals tab.
            table_fields = ['name', 'progress', 'priority', 'total',
                            'need-translation', 'suggestions']
            items = [make_goal_item(path_obj_goal, path_obj.pootle_path)
                     for path_obj_goal in path_obj_goals]
            template_vars.update({
                'table': {
                    'id': 'tp-goals',
                    'proportional': False,
                    'fields': table_fields,
                    'headings': get_table_headings(table_fields),
                    'items': items,
                },
                'path_obj_has_goals': True,
            })
        elif goal in path_obj_goals:
            # Then show the drill down view for the specified goal.
            table_fields = ['name', 'progress', 'total', 'need-translation',
                            'suggestions']

            template_vars.update({
                'table': {
                    'id': 'tp-goals',
                    'proportional': True,
                    'fields': table_fields,
                    'headings': get_table_headings(table_fields),
                    'items': get_goal_children(directory, goal),
                },
                'goal': goal,
                'goal_url': goal.get_drill_down_url_for_path(tp_pootle_path),
                'path_obj_has_goals': True,
            })
        else:
            # Then show the files tab.
            table_fields = ['name', 'progress', 'total', 'need-translation',
                            'suggestions']
            template_vars.update({
                'table': {
                    'id': 'tp-files',
                    'proportional': True,
                    'fields': table_fields,
                    'headings': get_table_headings(table_fields),
                    'items': get_children(directory),
                },
                'path_obj_has_goals': path_obj_has_goals,
            })
    elif goal is not None:
        template_vars.update({
            'goal': goal,
            'goal_url': goal.get_drill_down_url_for_path(tp_pootle_path),
        })

    if can_edit:
        if store is None:
            url_kwargs = {
                'language_code': language.code,
                'project_code': project.code,
            }
            add_tag_action_url = reverse('tp.ajax_add_tag', kwargs=url_kwargs)
        else:
            add_tag_action_url = reverse('pootle-store-ajax-add-tag',
                                         args=[path_obj.pk])

        if goal is None:
            edit_form = DescriptionForm(instance=translation_project)
            edit_form_action = reverse('pootle-tp-ajax-edit-settings',
                                       args=[language.code, project.code])
        else:
            edit_form = GoalForm(instance=goal)
            edit_form_action = reverse('pootle-tagging-ajax-edit-goal',
                                       args=[goal.slug])

        template_vars.update({
            'form': edit_form,
            'form_action': edit_form_action,
            'add_tag_form': TagForm(),
            'add_tag_action_url': add_tag_action_url,
        })

    return render_to_response(template, template_vars,
                              context_instance=RequestContext(request))


@require_POST
@ajax_required
@get_path_obj
@permission_required('administrate')
def ajax_remove_tag_from_tp(request, translation_project, tag_name):

    if tag_name.startswith("goal:"):
        translation_project.goals.remove(tag_name)
    else:
        translation_project.tags.remove(tag_name)

    return HttpResponse(status=201)


def _add_tag(request, translation_project, tag_like_object):
    if isinstance(tag_like_object, Tag):
        translation_project.tags.add(tag_like_object)
    else:
        translation_project.goals.add(tag_like_object)
    context = {
        'tp_tags': translation_project.tag_like_objects,
        'language': translation_project.language,
        'project': translation_project.project,
        'can_edit': check_permission('administrate', request),
    }
    response = render_to_response('translation_project/xhr_tags_list.html',
                                  context, RequestContext(request))
    response.status_code = 201
    return response


@require_POST
@ajax_required
@get_path_obj
@permission_required('administrate')
def ajax_add_tag_to_tp(request, translation_project):
    """Return an HTML snippet with the failed form or blank if valid."""

    add_tag_form = TagForm(request.POST)

    if add_tag_form.is_valid():
        new_tag_like_object = add_tag_form.save()
        return _add_tag(request, translation_project, new_tag_like_object)
    else:
        # If the form is invalid, perhaps it is because the tag (or goal)
        # already exists, so check if the tag (or goal) exists.
        try:
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
                'language_code': translation_project.language.code,
                'project_code': translation_project.project.code,
            }
            context = {
                'add_tag_form': add_tag_form,
                'add_tag_action_url': reverse('tp.ajax_add_tag',
                                              kwargs=url_kwargs)
            }
            return render_to_response('common/xhr_add_tag_form.html', context,
                                      RequestContext(request))


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

        'editor_extends': 'tp_base.html',
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
        'goal': request.GET.get('goal', ''),
    }

    return render_to_response('translation_project/export_view.html', ctx,
                              context_instance=RequestContext(request))


@ajax_required
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
        store = None
        directory = get_object_or_404(Directory, pootle_path=current_path)

    path_obj = store or directory
    path_stats = get_raw_stats(path_obj)
    context = {
        'check_failures': get_quality_check_failures(path_obj, path_stats),
        'trans_stats': get_translation_stats(path_obj, path_stats),
    }
    return render_to_response('translation_project/xhr-path_summary.html',
                              context, RequestContext(request))


@require_POST
@ajax_required
@get_path_obj
@permission_required('administrate')
def edit_settings(request, translation_project):
    form = DescriptionForm(request.POST, instance=translation_project)
    response = {}
    rcode = 400

    if form.is_valid():
        form.save()
        rcode = 200

        if translation_project.description:
            response["description"] = translation_project.description
        else:
            response["description"] = (u'<p class="placeholder muted">%s</p>' %
                                       _(u"No description yet."))
    context = {
        "form": form,
        "form_action": reverse('pootle-tp-ajax-edit-settings',
                               args=[translation_project.language.code,
                                     translation_project.project.code]),
    }
    t = loader.get_template('admin/general_settings_form.html')
    c = RequestContext(request, context)
    response['form'] = t.render(c)

    return HttpResponse(jsonify(response), status=rcode,
                        mimetype="application/json")


@get_path_obj
@permission_required('archive')
def export_zip(request, translation_project, file_path):
    translation_project.sync()
    pootle_path = translation_project.pootle_path + (file_path or '')

    archivename = '%s-%s' % (translation_project.project.code,
                             translation_project.language.code)

    if file_path.endswith('/'):
        file_path = file_path[:-1]

    if file_path:
        archivename += '-' + file_path.replace('/', '-')

    archivename += '.zip'
    export_path = os.path.join('POOTLE_EXPORT', translation_project.real_path,
                               archivename)
    abs_export_path = absolute_real_path(export_path)

    key = iri_to_uri("%s:export_zip" % pootle_path)
    last_export = cache.get(key)

    if (not (last_export and last_export == translation_project.get_mtime() and
        os.path.isfile(abs_export_path))):

        ensure_target_dir_exists(abs_export_path)
        stores = Store.objects.filter(pootle_path__startswith=pootle_path) \
                              .exclude(file='')
        translation_project.get_archive(stores, abs_export_path)
        cache.set(key, translation_project.get_mtime(),
                  settings.OBJECT_CACHE_TIMEOUT)

    return redirect('/export/' + export_path)


def unix_to_host_path(p):
    return os.sep.join(p.split('/'))


def host_to_unix_path(p):
    return '/'.join(p.split(os.sep))


def get_upload_path(translation_project, relative_root_dir, local_filename):
    """Gets the path of a translation file being uploaded securely, creating
    directories as necessary.
    """
    dir_path = os.path.join(translation_project.real_path,
                            unix_to_host_path(relative_root_dir))
    return relative_real_path(os.path.join(dir_path, local_filename))


def get_local_filename(translation_project, upload_filename):
    base, ext = os.path.splitext(upload_filename)
    new_ext = translation_project.project.get_file_extension()

    if new_ext == 'po' and translation_project.is_template_project:
        new_ext = 'pot'

    local_filename =  '%s.%s' % (base, new_ext)

    # Check if name is valid.
    if (os.path.basename(local_filename) != local_filename or
        local_filename.startswith(".")):
        raise ValueError(_("Invalid/insecure file name: %s", local_filename))

    # XXX: Leakage of the project layout information outside of
    # project_tree.py! The rest of Pootle shouldn't have to care
    # whether something is GNU-style or not.
    if (translation_project.file_style == "gnu" and
        not translation_project.is_template_project):

        language_code = translation_project.language.code
        if not direct_language_match_filename(language_code, local_filename):
            invalid_dict = {
                'local_filename': local_filename,
                'langcode': translation_project.language.code,
                'filetype': translation_project.project.get_file_extension(),
            }
            raise ValueError(_("Invalid GNU-style file name: "
                               "%(local_filename)s. It must match "
                               "'%(langcode)s.%(filetype)s'.", invalid_dict))
    return local_filename


def unzip_external(request, directory, django_file, overwrite):
    # Make a temporary directory to hold a zip file and its unzipped contents.
    from pootle_misc import ptempfile as tempfile
    tempdir = tempfile.mkdtemp(prefix='pootle')

    # Make a temporary file to hold the zip file.
    tempzipfd, tempzipname = tempfile.mkstemp(prefix='pootle', suffix='.zip')
    try:
        # Dump the uploaded file to the temporary file.
        try:
            os.write(tempzipfd, django_file.read())
        finally:
            os.close(tempzipfd)
        # Unzip the temporary zip file.
        import subprocess
        if subprocess.call(["unzip", tempzipname, "-d", tempdir]):
            import zipfile
            raise zipfile.BadZipfile(_("Error while extracting archive"))
        # Enumerate the temporary directory.
        maybe_skip = True
        prefix = tempdir
        for basedir, dirs, files in os.walk(tempdir):
            if maybe_skip and not files and len(dirs) == 1:
                try:
                    directory.child_dirs.get(name=dirs[0])
                    maybe_skip = False
                except Directory.DoesNotExist:
                    prefix = os.path.join(basedir, dirs[0])
                    continue
            else:
                maybe_skip = False

            for fname in files:
                # Read the contents of a file.
                fcontents = open(os.path.join(basedir, fname), 'rb').read()
                newfile = StringIO.StringIO(fcontents)
                newfile.name = os.path.basename(fname)
                # Get the filesystem path relative to the temporary directory.
                subdir = host_to_unix_path(basedir[len(prefix)+len(os.sep):])
                if subdir:
                    target_dir = directory.get_or_make_subdir(subdir)
                else:
                    target_dir = directory
                # Construct a full UNIX path relative to the current
                # translation project URL by attaching a UNIXified
                # 'relative_host_dir' to the root relative path, i.e. the path
                # from which the user is uploading the ZIP file.
                try:
                    upload_file(request, target_dir, newfile, overwrite)
                except ValueError:
                    logging.exception(u"Error adding file %s", fname)
    finally:
        # Clean up temporary file and directory used in try-block.
        import shutil
        os.unlink(tempzipname)
        shutil.rmtree(tempdir)


def unzip_python(request, directory, django_file, overwrite):
    import zipfile
    django_file.seek(0)
    archive = zipfile.ZipFile(django_file, 'r')
    # TODO: find a better way to return errors...
    try:
        prefix = ''
        maybe_skip = True
        for filename in archive.namelist():
            try:
                if filename[-1] == '/':
                    if maybe_skip:
                        try:
                            directory.child_dirs.get(name=filename[:-1])
                            maybe_skip = False
                        except Directory.DoesNotExist:
                            prefix = filename
                else:
                    maybe_skip = False
                    subdir = host_to_unix_path(os.path.dirname(filename[len(prefix):]))
                    if subdir:
                        target_dir = directory.get_or_make_subdir(subdir)
                    else:
                        target_dir = directory
                    newfile = StringIO.StringIO(archive.read(filename))
                    newfile.name = os.path.basename(filename)
                    upload_file(request, target_dir, newfile, overwrite)
            except ValueError:
                logging.exception(u"Error adding file %s", filename)
    finally:
        archive.close()


def upload_archive(request, directory, django_file, overwrite):
    # First we try to use "unzip" from the system, otherwise fall back to using
    # the slower zipfile module.
    try:
        unzip_external(request, directory, django_file, overwrite)
    except:
        unzip_python(request, directory, django_file, overwrite)


def overwrite_file(request, relative_root_dir, django_file, upload_path):
    """Overwrite with uploaded file."""
    upload_dir = os.path.dirname(absolute_real_path(upload_path))
    # Ensure that there is a directory into which we can dump the uploaded
    # file.
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Get the file extensions of the uploaded filename and the current
    # translation project.
    _upload_base, upload_ext = os.path.splitext(django_file.name)
    _local_base, local_ext = os.path.splitext(upload_path)
    # If the extension of the uploaded file matches the extension used in this
    # translation project, then we simply write the file to the disk.
    if upload_ext == local_ext:
        outfile = open(absolute_real_path(upload_path), "wb")
        try:
            outfile.write(django_file.read())
        finally:
            outfile.close()
            try:
                #FIXME: we need a way to delay reparsing
                store = Store.objects.get(file=upload_path)
                store.update(update_structure=True, update_translation=True)
            except Store.DoesNotExist:
                # newfile, delay parsing
                pass
    else:
        from translate.storage import factory
        newstore = factory.getobject(django_file, classes=factory_classes)
        if not newstore.units:
            return

        # If the extension of the uploaded file does not match the extension of
        # the current translation project, we create an empty file (with the
        # right extension).
        empty_store = factory.getobject(absolute_real_path(upload_path),
                                        classes=factory_classes)
        # And save it.
        empty_store.save()
        request.translation_project.scan_files(vcs_sync=False)
        # Then we open this newly created file and merge the uploaded file into
        # it.
        store = Store.objects.get(file=upload_path)
        #FIXME: maybe there is a faster way to do this?
        store.update(update_structure=True, update_translation=True,
                     store=newstore)
        store.sync(update_structure=True, update_translation=True,
                   conservative=False)


def upload_file(request, directory, django_file, overwrite, store=None):
    translation_project = request.translation_project
    tp_pootle_path_length = len(translation_project.pootle_path)
    relative_root_dir = directory.pootle_path[tp_pootle_path_length:]

    # for some reason factory checks explicitly for file existance and
    # if file is open, which makes it difficult to work with Django's
    # in memory uploads.
    #
    # setting _closed to False should work around this
    #FIXME: hackish, does this have any undesirable side effect?
    if getattr(django_file, '_closed', None) is None:
        try:
            django_file._closed = False
        except AttributeError:
            pass
    # factory also checks for _mode
    if getattr(django_file, '_mode', None) is None:
        try:
            django_file._mode = 1
        except AttributeError:
            pass
    # mode is an attribute not a property in Django 1.1
    if getattr(django_file, 'mode', None) is None:
        django_file.mode = 1

    if store and store.file:
        # Uploading to an existing file.
        pootle_path = store.pootle_path
        upload_path = store.real_path
    elif store:
        # Uploading to a virtual store.
        pootle_path = store.pootle_path
        upload_path = get_upload_path(translation_project, relative_root_dir,
                                      store.name)
    else:
        local_filename = get_local_filename(translation_project,
                                            django_file.name)
        pootle_path = directory.pootle_path + local_filename
        # The full filesystem path to 'local_filename'.
        upload_path = get_upload_path(translation_project, relative_root_dir,
                                      local_filename)
        try:
            store = translation_project.stores.get(pootle_path=pootle_path)
        except Store.DoesNotExist:
            store = None

    if (store is not None and overwrite == 'overwrite' and
        not check_permission('overwrite', request)):
        raise PermissionDenied(_("You do not have rights to overwrite files "
                                 "here."))

    if store is None and not check_permission('administrate', request):
        raise PermissionDenied(_("You do not have rights to upload new files "
                                 "here."))

    if overwrite == 'merge' and not check_permission('translate', request):
        raise PermissionDenied(_("You do not have rights to upload files "
                                 "here."))

    if overwrite == 'suggest' and not check_permission('suggest', request):
        raise PermissionDenied(_("You do not have rights to upload files "
                                 "here."))

    if store is None or (overwrite == 'overwrite' and store.file != ""):
        overwrite_file(request, relative_root_dir, django_file, upload_path)
        return

    if store.file and store.file.read() == django_file.read():
        logging.debug(u"identical file uploaded to %s, not merging",
                      store.pootle_path)
        return

    django_file.seek(0)
    from translate.storage import factory
    newstore = factory.getobject(django_file, classes=factory_classes)

    #FIXME: are we sure this is what we want to do? shouldn't we
    # differentiate between structure changing uploads and mere
    # pretranslate uploads?
    suggestions = overwrite == 'merge'
    notranslate = overwrite == 'suggest'
    allownewstrings = overwrite == 'overwrite' and store.file == ''

    store.mergefile(newstore, get_profile(request.user),
                    suggestions=suggestions, notranslate=notranslate,
                    allownewstrings=allownewstrings,
                    obsoletemissing=allownewstrings)
