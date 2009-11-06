#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of Virtaal.
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

from django.conf import settings
from django.utils.html import escape
from django.utils.translation import ugettext as _
from pootle_app.models.profile import get_profile

def get_title():
    return _(settings.TITLE)

def get_description():
    return _(settings.DESCRIPTION)

def getdoclang(language):
    """Get the language code that the docs should be displayed in."""

    # TODO: Determine the available languages programmatically.
    available_languages = ['en']
    if language in available_languages:
        return language
    else:
        return 'en'

def weblanguage(language):
    """Reformats the language code from locale style (pt_BR) to web
    style (pt-br)"""

    return language.replace('_', '-')


def completetemplatevars(templatevars, request, bannerheight=135):
    """fill out default values for template variables"""

    if not 'instancetitle' in templatevars:
        templatevars['instancetitle'] = get_title()
    templatevars['request'] = request
    if not 'mediaurl' in templatevars:
        templatevars['mediaurl'] = settings.MEDIA_URL
    if not 'enablealtsrc' in templatevars:
        templatevars['enablealtsrc'] = settings.ENABLE_ALT_SRC
    templatevars['uilanguage'] = weblanguage(request.LANGUAGE_CODE)
    try:
        templatevars['username'] = templatevars['username']
    except:
        templatevars['username'] = ''
    templatevars['canregister'] = settings.CAN_REGISTER
    templatevars['current_url'] = request.path_info
    if 'user' not in templatevars:
        templatevars['user'] = request.user
    if 'search' not in templatevars:
        templatevars['search'] = None
    templatevars['message'] = escape(request.GET.get('message', ''))

