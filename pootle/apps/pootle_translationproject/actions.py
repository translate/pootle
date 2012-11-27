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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from pootle_app.models.permissions import check_permission
from pootle_app.views.language import dispatch
from pootle_misc.baseurl import l
from pootle_misc.versioncontrol import hasversioning


# FIXME: Replace dispatch.* calls by django.core.urlresolvers.reverse

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


def translate_all(request, path_obj, **kwargs):
    text = _('Translate all')
    tooltip = _('Translate all the units independently of their status.')
    href = dispatch.translate(path_obj)

    return {
        'icon': 'icon-translate-all',
        'href': href,
        'text': text,
        'tooltip': tooltip,
    }


def translate_incomplete(request, path_obj, **kwargs):
    path_stats = kwargs.get('path_stats', None)

    if (not path_stats
        or not (path_stats['untranslated']['words'] > 0
                or path_stats['fuzzy']['words'] > 0)):
        return

    # Translators: This refers to the action of translating units that need
    # attention, i.e. are untranslated or fuzzy.
    text = _('Translate incomplete')
    tooltip = _('Translate all the units that need attention.')
    href = dispatch.translate(path_obj, state='incomplete')

    return {
        'icon': 'icon-translate-incomplete',
        'href': href,
        'text': text,
        'tooltip': tooltip,
    }


@directory
def download_zip(request, path_obj, **kwargs):
    if check_permission('archive', request):
        text = _('Download (.zip)')
        link = dispatch.download_zip(path_obj)

        return {
            'icon': 'icon-download',
            'href': link,
            'text': text,
        }


@store
def download_source(request, path_obj, **kwargs):
    href = None
    if path_obj.name.startswith("pootle-terminology"):
        text = _("Download XLIFF")
        tooltip = _("Download file in XLIFF format")
        href = l('%s/export/xlf' % path_obj.pootle_path)
    elif path_obj.translation_project.project.is_monolingual():
        text = _('Export')
        tooltip = _('Export translations')
    else:
        text = _('Download')
        tooltip = _('Download file')

    return {
        'icon': 'icon-download',
        'href': href or l('%s/download/' % path_obj.pootle_path),
        'text': text,
        'tooltip': tooltip,
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


def upload_zip(request, path_obj, **kwargs):
    if (check_permission('translate', request) or
        check_permission('suggest', request) or
        check_permission('overwrite', request)):
        text = _('Upload')
        tooltip = _('Upload translation files or archives in .zip format')
        link = '#'

        return {
            'icon': 'icon-upload',
            'class': 'js-overview-actions-upload',
            'href': link,
            'text': text,
            'tooltip': tooltip,
        }


@store
def update_from_vcs(request, path_obj, **kwargs):
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
def commit_to_vcs(request, path_obj, **kwargs):
    if (path_obj.abs_real_path and check_permission('commit', request) and
        hasversioning(path_obj.abs_real_path)):
        link = dispatch.commit(path_obj)
        text = _('Commit to VCS')

        return {
            'icon': 'icon-vcs-commit',
            'href': link,
            'text': text,
        }


def rescan_project_files(request, path_obj, **kwargs):
    if check_permission('administrate', request):
        tp = path_obj.translation_project
        link = reverse('tp.rescan', args=[tp.language.code, tp.project.code])
        text = _("Rescan project files")

        return {
            'icon': 'icon-rescan-files',
            'href': link,
            'text': text,
        }


def update_against_templates(request, path_obj, **kwargs):
    if check_permission('administrate', request):
        tp = path_obj.translation_project
        link = reverse('tp.update_against_templates', args=[tp.language.code,
                                                            tp.project.code])
        text = _("Update against templates")

        return {
            'icon': 'icon-update-templates',
            'href': link,
            'text': text,
        }


def delete_path_obj(request, path_obj, **kwargs):
    if check_permission('administrate', request):
        tp = path_obj.translation_project
        link = reverse('tp.delete_path_obj', args=[tp.language.code,
                                                   tp.project.code,
                                                   path_obj.path])

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
        {'group': 'translate-online', 'group_display': _("Translate online"),
         'actions': [translate_all, translate_incomplete]},
        {'group': 'translate-offline', 'group_display': _("Translate offline"),
         'actions': [download_source, download_zip, upload_zip]},
        {'group': 'manage', 'group_display': _("Manage"),
         'actions': [update_from_vcs, commit_to_vcs, rescan_project_files,
                     update_against_templates, delete_path_obj]},
    ]

    for group in groups:
        action_links = _gen_link_list(request, path_obj, group['actions'],
                                      **kwargs)

        if action_links:
            group['actions'] = action_links
            action_groups.append(group)

    return action_groups
