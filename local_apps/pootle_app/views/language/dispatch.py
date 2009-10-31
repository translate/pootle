#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
# 
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
from pootle_app.models.permissions import check_permission
from pootle_app import url_state, url_manip

################################################################################

class CommonState(url_state.State):
    """Stores state common to project index pages and translation pages."""
    editing       = url_state.BooleanValue('editing')

################################################################################

class ProjectIndexState(CommonState):
    show_checks   = url_state.BooleanValue('show_checks')

################################################################################

class TranslatePageState(CommonState):
    # Display state
    view_mode     = url_state.ChoiceValue('view_mode', ('view', 'review', 'translate', 'raw'))
    # Position state
    store         = url_state.Value('store')
    item          = url_state.IntValue('item', 0)
    # Search state
    match_names   = url_state.ListValue('match_names')

def get_store(request):
    basename = url_manip.basename(request.path_info)
    if basename == 'translate.html':
        if 'store' in request.POST:
            return request.POST['store']
        else:
            return request.GET.get('store', '')
    
    else:
        return request.path_info

################################################################################

def translate(request, path, **kwargs):
    params = TranslatePageState(request.GET, **kwargs)
    # In Pootle, URLs ending in translate.html are used when the user
    # translates all files in a directory (for example, if the user is
    # going through all fuzzy translations in a directory). If this is
    # the case, we need to pass the current store name in the 'store'
    # GET variable so that Pootle will know where to continue from
    # when the user clicks submit/skip/suggest on a translation
    # unit. But otherwise the store name is the last component of the
    # path name and we don't need to pass the 'store' GET variable.
    if path[-1] == '/':
        path = path + 'translate.html'
    else:
        params.store = None
        
    if (check_permission('translate', request) or check_permission('suggest', request)) and \
           'view_mode' not in kwargs:
        params.view_mode = 'translate'
    return url_manip.make_url(path, params.encode())

def review(request, path, **kwargs):
    params = TranslatePageState(request.GET, **kwargs)
    # In Pootle, URLs ending in translate.html are used when the user
    # translates all files in a directory (for example, if the user is
    # going through all fuzzy translations in a directory). If this is
    # the case, we need to pass the current store name in the 'store'
    # GET variable so that Pootle will know where to continue from
    # when the user clicks submit/skip/suggest on a translation
    # unit. But otherwise the store name is the last component of the
    # path name and we don't need to pass the 'store' GET variable.
    if path[-1] == '/':
        path = path + 'translate.html'
    else:
        params.store = None
        
    if 'view_mode' not in kwargs:
        params.view_mode = 'review'
    return url_manip.make_url(path, params.encode())

def show_directory(request, directory_path, **kwargs):
    params = ProjectIndexState(request.GET, **kwargs).encode()
    return url_manip.make_url(directory_path, params)

def translation_project_admin(translation_project):
    return translation_project.directory.pootle_path + 'admin.html'

def open_language(request, code):
    return '/%s/' % code

def open_translation_project(request, language_code, project_code):
    return '/%s/%s/' % (language_code, project_code)

def download_zip(request, path_obj):
    if path_obj.is_dir:
        current_folder = path_obj.pootle_path
    else:
        current_folder = path_obj.parent.pootle_path
    # FIXME: ugly URL, django.core.urlresolvers.reverse() should work
    archive_name = "%sexport/zip" % current_folder
    return archive_name

def export(request, pootle_path, format):
    return '%s/export/%s' % (pootle_path, format)

def commit(request, path_obj):
    params = ProjectIndexState(request.GET).encode()
    return  url_manip.make_url(path_obj.pootle_path + '/commit', params)

def update(request, path_obj):
    params = ProjectIndexState(request.GET).encode()
    return  url_manip.make_url(path_obj.pootle_path + '/update', params)
