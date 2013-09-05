#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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

"""Actions available for the translation project overview page."""

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from pootle_app.models.permissions import check_permission


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
                       args=[tp.language.code, tp.project.code, path_obj.path])

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

# TODO delete
def _gen_link_list(request, path_obj, link_funcs, **kwargs):
    """Generates a list of links based on :param:`link_funcs`."""
    links = []

    for link_func in link_funcs:
        link = link_func(request, path_obj, **kwargs)

        if link is not None:
            links.append(link)

    return links

# TODO delete
def action_groups(request, path_obj, **kwargs):
    """Returns a list of action links grouped for the overview page.

    :param request: A :class:`~django.http.HttpRequest` object.
    :param path_obj: A :class:`~pootle_app.models.Directory` or
        :class:`~pootle_app.models.Store` object.
    :param kwargs: Extra keyword arguments passed to the underlying functions.
    """
    action_groups = []

    groups = [
        {'group': 'manage', 'group_display': _("Manage"),
         'actions': [rescan_project_files, update_against_templates,
                     delete_path_obj]
        },
    ]

    for group in groups:
        action_links = _gen_link_list(request, path_obj, group['actions'],
                                      **kwargs)

        if action_links:
            group['actions'] = action_links
            action_groups.append(group)

    return action_groups
