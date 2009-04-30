#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

from django.utils.translation import ugettext as _

from pootle_app.models              import Language, Project, TranslationProject
from pootle_app.lib.util            import redirect
from pootle_app.views               import indexpage, pagelayout
from pootle_app.views.util          import render_to_kid, render_jtoolkit, \
    KidRequestContext, init_formset_from_data, choices_from_models, selected_model

def get_project(f):
    def decorated_f(request, project_code, *args, **kwargs):
        try:
            project = Project.objects.get(code=project_code)
            return f(request, project, *args, **kwargs)
        except Project.DoesNotExist:
            return redirect('/', message=_('The project "%s" is not defined for this Pootle installation' % project_code))
    return decorated_f

@get_project
def view(request, project, _path_var):
    return render_jtoolkit(indexpage.ProjectLanguageIndex(project, request))
