#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404

from pootle_app.views.admin import util
from pootle_app.views.language import search_forms
from pootle_app.views.language import navbar_dict
from pootle_store.models import Store
from pootle_app.models.translation_project import TranslationProject


def view(request, language_code, project_code):
    translation_project = get_object_or_404(TranslationProject, language__code=language_code, project__code=project_code)
    queryset = translation_project.stores
    model_args = {}
    model_args['title'] = _("Files")
    model_args['submitname'] = "changestores"
    model_args['formid'] = "stores"
    # Commented for now
    #model_args['search'] = search_forms.get_search_form(request)
    #model_args['navitems'] = [navbar_dict.make_directory_navbar_dict(request, translation_project.directory)]
    link = "%s"
    return util.edit(request, 'language/tp_admin_files.html', Store, model_args,
                     link, linkfield='pootle_path', queryset=queryset,
                     can_delete=True)
