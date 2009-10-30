#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from pootle_app.models.directory import Directory
from pootle_app.views.language.admin_permissions import process_update as process_permission_update

from util import user_is_admin

@user_is_admin
def view(request):
    permission_set_formset = process_permission_update(request, Directory.objects.root)

    template_vars = {
        "norights_text":          _("You do not have the rights to administer site permissions."),
        "permission_set_formset": permission_set_formset,
        "hide_fileadmin_links":   True,
    }
    return render_to_response("admin/admin_general_permissions.html", template_vars, context_instance=RequestContext(request))
