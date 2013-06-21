#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
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

from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _

from pootle.core.decorators import (get_translation_project,
                                    set_tp_request_context)
from pootle_app.models.directory import Directory
from pootle_app.models.permissions import check_permission
from pootle_store.views import get_failing_checks, get_view_units


@get_translation_project
@set_tp_request_context
def get_failing_checks_dir(request, translation_project, dir_path):
    if dir_path:
        pootle_path = translation_project.pootle_path + dir_path
        pathobj = Directory.objects.get(pootle_path=pootle_path)
    else:
        pathobj = translation_project

    return get_failing_checks(request, pathobj)


@get_translation_project
@set_tp_request_context
def get_view_units_dir(request, translation_project, dir_path):
    if not check_permission("view", request):
        raise PermissionDenied(_("You do not have rights to access this "
                                 "translation project."))

    units_query = translation_project.units
    if dir_path:
        pootle_path = translation_project.pootle_path + dir_path
        units_query = units_query.filter(store__pootle_path__startswith=pootle_path)

    return get_view_units(request, units_query, store=False)
