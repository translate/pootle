#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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

"""Actions available for the translation project overview page."""

from django.utils.translation import ugettext as _

from pootle_app.models.permissions import check_permission
from pootle_app.views.language import dispatch
from pootle_misc.versioncontrol import hasversioning


# FIXME: Replace dispatch.* calls by django.core.urlresolvers.reverse
# TODO: Add missing actions: bug 2415

def directory(fn):
    """Decorator that returns links only for directory objects."""
    def wrapper(request, path_obj):
        if not path_obj.is_dir:
            return

        return fn(request, path_obj)

    return wrapper


def store(fn):
    """Decorator that returns links only for store objects."""
    def wrapper(request, path_obj):
        if path_obj.is_dir:
            return

        return fn(request, path_obj)

    return wrapper


@directory
def download_zip(request, path_obj):
    if check_permission('archive', request):
        text = _('Download (.zip)')
        link = dispatch.download_zip(path_obj)

        return {
            'icon': 'icon-download',
            'href': link,
            'text': text,
        }


def upload_zip(request, path_obj):
    if (check_permission('translate', request) or
        check_permission('suggest', request) or
        check_permission('overwrite', request)):
        text = _('Upload (.zip)')
        link = '#'

        return {
            'icon': 'icon-upload',
            'class': 'js-overview-actions-upload',
            'href': link,
            'text': text,
        }


@store
def update_from_vcs(request, path_obj):
    if (path_obj.abs_real_path and check_permission('commit', request) and
        hasversioning(path_obj.abs_real_path)):
        link = dispatch.update(path_obj)
        text = _('Update from VCS')

        return {
            'icon': 'icon-vcs-update',
            'href': link,
            'text': text,
        }


@store
def commit_to_vcs(request, path_obj):
    if (path_obj.abs_real_path and check_permission('commit', request) and
        hasversioning(path_obj.abs_real_path)):
        link = dispatch.commit(path_obj)
        text = _('Commit to VCS')

        return {
            'icon': 'icon-vcs-commit',
            'href': link,
            'text': text,
        }


@store
def download_xliff(request, path_obj):
    if path_obj.translation_project.project.localfiletype == 'xlf':
        return

    text = _('Translate offline')
    tooltip = _('Download XLIFF file for offline translation')
    href = dispatch.export(path_obj.pootle_path, 'xlf')

    return {
        'icon': 'icon-translate-download',
        'href': href,
        'text': text,
        'tooltip': tooltip,
    }


@store
def download_sources(request, path_obj):
    if path_obj.translation_project.project.is_monolingual():
        text = _('Export')
        tooltip = _('Export translations')
    else:
        text = _('Download')
        tooltip = _('Download file')

    return {
        'icon': 'icon-download',
        'href': '%s/download/' % path_obj.pootle_path,
        'text': text,
        'tooltip': tooltip,
    }


def _gen_link_list(request, path_obj, link_funcs):
    """Generates a list of links based on ``link_funcs``."""
    links = []

    for link_func in link_funcs:
        link = link_func(request, path_obj)

        if link is not None:
            links.append(link)

    return links


def action_groups(request, path_obj):
    """Returns a list of action links grouped for the overview page."""
    action_groups = []

    groups = [
        {'group': 'translate-offline', 'group_display': _("Translate offline"),
         'actions': [download_zip, upload_zip]},
        {'group': 'manage', 'group_display': _("Manage"),
         'actions': [update_from_vcs, commit_to_vcs]},
        {'group': 'download-source', 'group_display': _("Download sources"),
         'actions': [download_sources]},
    ]

    for group in groups:
        action_links = _gen_link_list(request, path_obj, group['actions'])

        if action_links:
            group['actions'] = action_links
            action_groups.append(group)

    return action_groups
