#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright 2006-2014 Zuza Software Foundation
#  Copyright 2013 Evernote Corporation
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

from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle.core.decorators import admin_required
from pootle_app.forms import GeneralSettingsForm
from pootle_misc.siteconfig import load_site_config


@admin_required
def view(request):
    siteconfig = load_site_config()

    if request.POST:
        setting_form = GeneralSettingsForm(siteconfig, data=request.POST)

        if setting_form.is_valid():
            setting_form.save()
    else:
        setting_form = GeneralSettingsForm(siteconfig)

    ctx = {
        'form': setting_form,
    }
    return render_to_response('admin/settings.html', ctx,
                              context_instance=RequestContext(request))
