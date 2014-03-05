#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2014 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from pootle.core.decorators import admin_required
from pootle_app.models.directory import Directory
from pootle_app.views.admin.permissions import admin_permissions


@admin_required
def view(request):
    directory = Directory.objects.root
    ctx = {
        'directory': directory,
    }
    return admin_permissions(request, directory, "admin/permissions.html", ctx)
