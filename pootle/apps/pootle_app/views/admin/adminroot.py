# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.decorators import admin_required
from pootle_app.models.directory import Directory
from pootle_app.views.admin.permissions import admin_permissions


@admin_required
def view(request):
    directory = Directory.objects.root
    ctx = {
        'page': 'admin-permissions',
        'directory': directory,
    }
    return admin_permissions(request, directory, "admin/permissions.html", ctx)
