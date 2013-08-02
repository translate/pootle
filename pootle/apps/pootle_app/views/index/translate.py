#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.helpers import get_translation_context


@get_path_obj
@permission_required('view')
def view(request, root_dir):
    request.pootle_path = root_dir.pootle_path
    request.ctx_path = root_dir.pootle_path
    request.resource_path = ''

    request.store = None
    request.directory = root_dir

    language = None
    project = None

    context = get_translation_context(request)
    context.update({
        'language': language,
        'project': project,

        'editor_extends': 'main_base.html',
        'editor_body_id': 'main-translate',
    })

    return render_to_response('editor/main.html', context,
                              context_instance=RequestContext(request))
