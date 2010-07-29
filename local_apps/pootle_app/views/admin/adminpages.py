#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Copyright 2006-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This file is somewhat based on the older Pootle/translatepage.py
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.


from pootle_app.views.admin.util import user_is_admin
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle_misc.siteconfig import load_site_config
from pootle_app.forms import GeneralSettingsForm

@user_is_admin
def view(request):
    siteconfig = load_site_config()
    if request.POST:
        setting_form = GeneralSettingsForm(siteconfig, data=request.POST)
        if setting_form.is_valid():
            setting_form.save()
            load_site_config()
    else:
        setting_form = GeneralSettingsForm(siteconfig)

    template = 'admin/admin_general_settings.html'
    template_vars = {
        'form': setting_form,
        }
    return render_to_response(template, template_vars, context_instance=RequestContext(request))
