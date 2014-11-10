#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Zuza Software Foundation
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

"""Actions available for the translation project overview page."""

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from pootle.core.url_helpers import split_pootle_path
from pootle_app.models.permissions import check_permission
from pootle_misc.versioncontrol import hasversioning
from pootle.scripts import actions


def directory(fn):
    """Decorator that returns links only for directory objects."""
    def wrapper(request, path_obj, **kwargs):
        if not path_obj.is_dir:
            return

        return fn(request, path_obj)

    return wrapper


def store(fn):
    """Decorator that returns links only for store objects."""
    def wrapper(request, path_obj, **kwargs):
        if path_obj.is_dir:
            return

        return fn(request, path_obj)

    return wrapper


@directory
def download_zip(request, path_obj, **kwargs):
    if check_permission('archive', request):
        if not path_obj.is_dir:
            path_obj = path_obj.parent

        language_code = path_obj.translation_project.language.code
        project_code = path_obj.translation_project.project.code

        return {
            'icon': 'icon-download',
            'href': reverse('pootle-tp-export-zip',
                            args=[language_code, project_code, path_obj.path]),
            'text': _('Download (.zip)'),
        }


@store
def download_source(request, path_obj, **kwargs):
    href = None
    if path_obj.name.startswith("pootle-terminology"):
        text = _("Download XLIFF")
        tooltip = _("Download file in XLIFF format")
        href = reverse('pootle-store-export-xliff',
                       args=[path_obj.pootle_path])
    elif path_obj.translation_project.project.is_monolingual:
        text = _('Export')
        tooltip = _('Export translations')
    else:
        text = _('Download')
        tooltip = _('Download file')

    return {
        'icon': 'icon-download',
        'href': href or reverse('pootle-store-download',
                                args=[path_obj.pootle_path]),
        'text': text,
        'tooltip': tooltip,
    }


@store
def download_xliff(request, path_obj):
    if (path_obj.translation_project.project.localfiletype == 'xlf' or
        path_obj.name.startswith("pootle-terminology")):
        return

    return {
        'icon': 'icon-download',
        'href': reverse('pootle-store-export-xliff',
                        args=[path_obj.pootle_path]),
        'text': _("Download XLIFF"),
        'tooltip': _('Download XLIFF file for offline translation'),
    }


def upload_zip(request, path_obj, **kwargs):
    if (check_permission('translate', request) or
        check_permission('suggest', request) or
        check_permission('overwrite', request)):
        return {
            'icon': 'icon-upload',
            'class': 'js-popup-inline',
            'href': '#upload',
            'text': _('Upload'),
            'tooltip': _('Upload translation files or archives in .zip '
                         'format'),
        }


@store
def update_from_vcs(request, path_obj, **kwargs):
    if (path_obj.abs_real_path and check_permission('commit', request) and
        hasversioning(path_obj.abs_real_path)):
        link = reverse('pootle-vcs-update',
                       args=split_pootle_path(path_obj.pootle_path))
        text = _('Update from VCS')

        return {
            'icon': 'icon-vcs-update',
            'href': link,
            'text': text,
        }


@store
def commit_to_vcs(request, path_obj, **kwargs):
    if (path_obj.abs_real_path and check_permission('commit', request) and
        hasversioning(path_obj.abs_real_path)):
        link = reverse('pootle-vcs-commit',
                       args=split_pootle_path(path_obj.pootle_path))
        text = _('Commit to VCS')

        return {
            'icon': 'icon-vcs-commit',
            'href': link,
            'text': text,
        }


@directory
def update_dir_from_vcs(request, path_obj, **kwargs):
    if (path_obj.get_real_path() and check_permission('commit', request) and
            hasversioning(path_obj.get_real_path())):
        link = reverse('pootle-vcs-update',
                       args=split_pootle_path(path_obj.pootle_path))
        # Translators: "all" here refers to all files and sub directories in a directory/project.
        text = _('Update all from VCS')

        return {
            'icon': 'icon-vcs-update',
            'href': link,
            'text': text,
        }


@directory
def commit_dir_to_vcs(request, path_obj, **kwargs):
    if (path_obj.get_real_path() and check_permission('commit', request) and
            hasversioning(path_obj.get_real_path())):
        link = reverse('pootle-vcs-commit',
                       args=split_pootle_path(path_obj.pootle_path))
        # Translators: "all" here refers to all files and sub directories in a directory/project.
        text = _('Commit all to VCS')

        return {
            'icon': 'icon-vcs-commit',
            'href': link,
            'text': text,
        }


def rescan_project_files(request, path_obj, **kwargs):
    if check_permission('administrate', request):
        tp = path_obj.translation_project
        link = reverse('pootle-tp-rescan',
                       args=[tp.language.code, tp.project.code])
        text = _("Rescan project files")

        return {
            'icon': 'icon-rescan-files',
            'href': link,
            'text': text,
        }


def update_against_templates(request, path_obj, **kwargs):
    if check_permission('administrate', request):
        tp = path_obj.translation_project
        link = reverse('pootle-tp-update-against-templates',
                       args=[tp.language.code, tp.project.code])
        text = _("Update against templates")

        return {
            'icon': 'icon-update-templates',
            'href': link,
            'text': text,
        }


def delete_path_obj(request, path_obj, **kwargs):
    if check_permission('administrate', request):
        tp = path_obj.translation_project
        link = reverse('pootle-tp-delete-path-obj',
                       args=[tp.language.code, tp.project.code, request.path])

        if path_obj.is_dir:
            text = _("Delete this folder...")
        else:
            text = _("Delete this file...")

        return {
            'icon': 'icon-delete-path',
            'class': 'js-overview-actions-delete-path',
            'href': link,
            'text': text,
        }


def _gen_link_list(request, path_obj, link_funcs, **kwargs):
    """Generates a list of links based on :param:`link_funcs`."""
    links = []

    for link_func in link_funcs:
        link = link_func(request, path_obj, **kwargs)

        if link is not None:
            links.append(link)

    return links


def action_groups(request, path_obj, **kwargs):
    """Returns a list of action links grouped for the overview page.

    :param request: A :class:`~django.http.HttpRequest` object.
    :param path_obj: A :class:`~pootle_app.models.Directory` or
        :class:`~pootle_app.models.Store` object.
    :param kwargs: Extra keyword arguments passed to the underlying functions.
    """
    action_groups = []

    groups = [
        {
            'group': 'translate-offline',
            'group_display': _("Translate offline"),
            'actions': [
                download_source,
                download_xliff,
                download_zip,
                upload_zip,
            ],
        },
        {
            'group': 'manage',
            'group_display': _("Manage"),
            'actions': [
                update_from_vcs,
                commit_to_vcs,
                update_dir_from_vcs,
                commit_dir_to_vcs,
                rescan_project_files,
                update_against_templates,
                delete_path_obj,
            ],
        },
    ]

    if path_obj.is_dir:
        act = actions.TranslationProjectAction
    else:
        act = actions.StoreAction

    for ext in act.instances():
        if ext.is_active(request):
            group = ext.category.lower().replace(' ', '-')
            for grp in groups:
                if grp['group'] == group:
                    grp['actions'].append(ext.get_link_func())
                    break
            else:
                groups.append({'group': group, 'group_display': _(ext.category),
                               'actions': [ext.get_link_func()]})

    for group in groups:
        action_links = _gen_link_list(request, path_obj, group['actions'],
                                      **kwargs)

        if action_links:
            group['actions'] = action_links
            action_groups.append(group)

    return action_groups
