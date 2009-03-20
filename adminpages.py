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
from Pootle import pagelayout
from Pootle import pan_app


class AdminPage(pagelayout.PootlePage):
    """page for administering pootle..."""

    def __init__(self, request):
        self.request = request
        templatename = 'adminindex'
        instancetitle = pan_app.get_title()
        text = self.gettext(request)
        templatevars = {
            'options': self.getoptions(),
            'pagetitle': _('Pootle Admin Page'),
            'instancetitle': instancetitle,
            'text': text,
            }
        pagelayout.PootlePage.__init__(self, templatename, templatevars,
                                       request)

    def gettext(self, request):
        """Localize the text"""

        text = {}
        text['home'] = _('Home')
        text['users'] = _('Users')
        text['languages'] = _('Languages')
        text['projects'] = _('Projects')
        text['generaloptions'] = _('General options')
        text['option'] = _('Option')
        text['currentvalue'] = _('Current value')
        text['savechanges'] = _('Save changes')
        return text

    def getoptions(self):
        optiontitles = {
            'TITLE': _('Title'),
            'DESCRIPTION': _('Description'),
            'MEDIA_URL': _('Media URL'),
            'HOMEPAGE': _('Home Page'),
            }
        option_values = {'TITLE': pan_app.get_title(),
                         'DESCRIPTION': pan_app.get_description()}
        options = []
        for (optionname, optiontitle) in optiontitles.items():
            optionvalue = getattr(settings, optionname,
                                  option_values.get(optionname, ''))
            option = {'name': 'option-%s' % optionname, 'title': optiontitle,
                      'value': optionvalue}
            options.append(option)
        return options


