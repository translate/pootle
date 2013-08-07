#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright 2006-2012 Zuza Software Foundation
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

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import loader, RequestContext

from pootle.core.decorators import admin_required
from pootle_app.forms import GeneralSettingsForm
from pootle_misc.siteconfig import load_site_config
from pootle_misc.util import jsonify, ajax_required


@admin_required
def view(request):
    siteconfig = load_site_config()
    if request.POST:
        setting_form = GeneralSettingsForm(siteconfig, data=request.POST)

        if setting_form.is_valid():
            setting_form.save()
    else:
        setting_form = GeneralSettingsForm(siteconfig)

    template = 'admin/admin_general_settings.html'
    template_vars = {
        'form': setting_form,
    }
    return render_to_response(template, template_vars,
                              context_instance=RequestContext(request))


@ajax_required
@admin_required
def edit_settings(request):
    """Saves the site's general settings."""
    siteconfig = load_site_config()
    form = GeneralSettingsForm(siteconfig, data=request.POST)

    response = {}
    rcode = 400

    if form.is_valid():
        form.save()
        rcode = 200

        the_html = u"".join([
            u"<div>", form.cleaned_data['DESCRIPTION'], "</div>"
        ])

        response["description"] = the_html

    context = {
        "form": form,
        "form_action": "/admin/edit_settings.html"
    }
    t = loader.get_template('admin/general_settings_form.html')
    c = RequestContext(request, context)
    response['form'] = t.render(c)

    return HttpResponse(jsonify(response), status=rcode,
                        mimetype="application/json")
