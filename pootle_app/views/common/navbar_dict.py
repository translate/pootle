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

from pootle_app.url_manip import URL, read_all_state
from pootle_app.views.common import item_dict
from pootle_app.permissions import check_permission

from Pootle.i18n.jtoolkit_i18n import tr_lang

def make_admin(request, project_url):
    if check_permission('admin', request):
        return {'href': project_url.child('admin.html').as_relative_to_path_info(request),
                'text': _('Admin')}
    else:
        return None

def make_pathlinks(request, project_url, url, links):
    if url.path != project_url.path:
        links.append({'href': url.as_relative_to_path_info(request),
                      'text': url.basename})
        return make_pathlinks(request, project_url, url.parent, links)
    else:
        return list(reversed(links))

def make_navbar_actions(request, url):
    return {
        'basic':    [item_dict.make_toggle_link(request, url, 'editing',
                                                _("Show Editing Functions"),
                                                _("Show Statistics"))],
        'extended': [],
        'goalform': []
        }

def make_navbar_path_dict(request, url):
    root = request.translation_project.directory
    plain_url   = URL(root.pootle_path, read_all_state({}))
    project_url = URL(root.pootle_path, url.state)
    new_url     = URL(url.path, read_all_state({}))
    new_url.state['search'] = url.state['search']
    return {
        'admin':     make_admin(request, project_url),
        'language':  {'href': plain_url.parent.as_relative_to_path_info(request), 
                      'text': tr_lang(request.translation_project.language.fullname)},
        'project':   {'href': plain_url.as_relative_to_path_info(request),
                      'text': request.translation_project.project.fullname},
        'pathlinks': make_pathlinks(request, project_url, new_url, []) }

def make_directory_navbar_dict(request, directory, url_state):
    result = item_dict.make_directory_item(request, directory, url_state)
    url = URL(directory.pootle_path, url_state)
    result.update({
            'path':    make_navbar_path_dict(request, url),
            'actions': make_navbar_actions(request, url) })
    del result['title']
    return result

def make_store_navbar_dict(request, store, url_state):
    result = item_dict.make_store_item(request, store, url_state)
    url = URL(store.pootle_path, url_state)
    result.update({
            'path':    make_navbar_path_dict(request, url),
            'actions': {'basic': [], 'extended': [], 'goalform': []} })
    del result['title']
    return result
