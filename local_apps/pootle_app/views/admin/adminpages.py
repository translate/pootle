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

from django.conf import settings
from django.utils.translation import ugettext as _
N_ = _

from pootle_app.views import pagelayout

from util import user_is_admin
from django.shortcuts import render_to_response
from django.template import RequestContext
from pootle_app.forms import GeneralSettingsForm

from djblets.siteconfig.models import SiteConfiguration
siteconfig = SiteConfiguration.objects.get_current()

def gettext():
    """Localize the text"""

    text = {}
    text['home'] = _('Home')
    text['admin'] = _("Main admin page"),
    text['users'] = _('Users')
    text['languages'] = _('Languages')
    text['projects'] = _('Projects')
    text['generaloptions'] = _('General options')
    text['option'] = _('Option')
    text['currentvalue'] = _('Current value')
    text['savechanges'] = _('Save changes')
    return text

def getoptions():
    optiontitles = {
        'TITLE': _('Title'),
        'DESCRIPTION': _('Description'),
        'MEDIA_URL': _('Media URL'),
        'HOMEPAGE': _('Home Page'),
        }
    option_values = {'TITLE': pagelayout.get_title(),
                     'DESCRIPTION': pagelayout.get_description()}
    options = []
    for (optionname, optiontitle) in optiontitles.items():
        optionvalue = getattr(settings, optionname,
                              option_values.get(optionname, ''))
        option = {'name': 'option-%s' % optionname, 'title': optiontitle,
                  'value': optionvalue}
        options.append(option)
    return options

@user_is_admin
def view(request, path):
    if request.POST:
        post = request.POST.copy()
        setting_form = GeneralSettingsForm(siteconfig, data=post)
        if setting_form.is_valid():
            setting_form.save()
    else:
        setting_form = GeneralSettingsForm(siteconfig)
    template = 'admin/adminindex.html'
    instancetitle = pagelayout.get_title()
    text = gettext()
    template_vars = {
        'options': getoptions(),
        'pagetitle': _('Pootle Admin Page'),
        'instancetitle': instancetitle,
        'text': text,
        'form': setting_form,
        }
    return render_to_response(template, template_vars, context_instance=RequestContext(request))
