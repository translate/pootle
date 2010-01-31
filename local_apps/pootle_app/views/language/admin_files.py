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
from django.forms.models import BaseModelFormSet

from pootle_app.views.admin import util
from pootle_app.views.language import search_forms
from pootle_app.views.language import navbar_dict
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject
from pootle_app import project_tree


class StoreFormset(BaseModelFormSet):
    def save_existing_objects(self, commit=True):
        result = super(StoreFormset, self).save_existing_objects(commit)
        for store in self.deleted_objects:
            #hackish: we disabled deleting files when field is
            # deleted except for when value is being overwritten, but
            # this form is the only place in pootle where actual file
            # system files should be deleted
            store.file.storage.delete(store.file.name)        
        return result


@util.has_permission('administrate')
def view(request, translation_project):
    queryset = translation_project.stores

    try:
        template_translation_project = TranslationProject.objects.get(project=translation_project.project,
                                                                      language__code='templates')
        if 'template_update' in request.GET:
            project_tree.convert_templates(template_translation_project, translation_project)
    except TranslationProject.DoesNotExist:
        pass
    
    if 'scan_files' in request.GET:
        project_tree.scan_translation_project_files(translation_project)


    model_args = {}
    model_args['title'] = _("Files")
    model_args['submitname'] = "changestores"
    model_args['formid'] = "stores"
    model_args['search'] = search_forms.get_search_form(request)
    model_args['navitems'] = [navbar_dict.make_directory_navbar_dict(request, translation_project.directory)]
    model_args['feed_path'] = translation_project.directory.pootle_path[1:]
    link = "%s"
    return util.edit(request, 'language/tp_admin_files.html', Store, model_args,
                     link, linkfield='pootle_path', queryset=queryset,
                     formset=StoreFormset, can_delete=True, extra=0)
