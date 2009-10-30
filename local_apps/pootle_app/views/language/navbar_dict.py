#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

"""Helper methods for the navigation bar."""

from django.utils.translation import ugettext as _

from pootle_app import url_manip
from pootle_app.models.permissions import check_permission
from pootle_app.views.language import dispatch
from pootle_app.views.language.item_dict import directory_translate_links, directory_review_links

from pootle.i18n.gettext import tr_lang

import item_dict

def make_directory_pathlinks(request, project_url, url, links):
    if url != project_url:
        links.append({'href': dispatch.show_directory(request, url),
                      'text': url_manip.basename(url)})
        return make_directory_pathlinks(request, project_url, url_manip.parent(url), links)
    else:
        return list(reversed(links))

def make_store_pathlinks(request, project_url, store, links):
    links = make_directory_pathlinks(request, project_url, url_manip.parent(store.pootle_path), [])
    links.append({'href': dispatch.translate(request, store.pootle_path),
                  'text': store.name})
    return links

def make_directory_actions(request, links_required=None):
    directory = request.translation_project.directory
    if links_required == 'translate':
        return directory_translate_links(request, directory)
    elif links_required == 'review':
        return directory_review_links(request, directory)
        

def make_navbar_path_dict(request, path_links=None):
    def make_admin(request):
        if check_permission('admin', request):
            return {'href': dispatch.translation_project_admin(request.translation_project),
                    'text': _('Admin')}
        else:
            return None

    language     = request.translation_project.language
    project      = request.translation_project.project
    return {
        'admin':     make_admin(request),
        'language':  {'href': dispatch.open_language(request, language.code),
                      'text': tr_lang(language.fullname)},
        'project':   {'href': dispatch.open_translation_project(request, language.code, project.code),
                      'text': project.fullname},
        'pathlinks': path_links }

def make_directory_navbar_dict(request, directory, links_required=None):
    result = item_dict.make_directory_item(request, directory, links_required)
    project_url = request.translation_project.directory.pootle_path
    path_links = make_directory_pathlinks(request, project_url, directory.pootle_path, [])
    if links_required:
        actions = make_directory_actions(request, links_required)
    else:
        actions = []
    result.update({
            'path':    make_navbar_path_dict(request, path_links),
            'actions': actions })
    del result['title']
    return result

def make_store_navbar_dict(request, store):
    result = item_dict.make_store_item(request, store)
    project_url = request.translation_project.directory.pootle_path
    path_links = make_store_pathlinks(request, project_url, store, [])
    result.update({
            'path':    make_navbar_path_dict(request, path_links),
            'actions': {'basic': [], 'extended': [],} })
    del result['title']
    return result
