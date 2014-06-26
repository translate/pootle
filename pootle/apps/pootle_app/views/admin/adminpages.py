#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright 2006-2014 Zuza Software Foundation
#  Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
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

from django.shortcuts import render

from pootle.core.decorators import admin_required
from pootle_app.forms import GeneralSettingsForm
from pootle_app.models.pootle_site import PootleSite


@admin_required
def view(request):
    site = PootleSite.objects.get_current()

    if request.POST:
        setting_form = GeneralSettingsForm(data=request.POST, instance=site)

        if setting_form.is_valid():
            setting_form.save()
    else:
        setting_form = GeneralSettingsForm(instance=site)

    ctx = {
        'form': setting_form,
    }
    return render(request, "admin/settings.html", ctx)
