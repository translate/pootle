#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Copyright 2004-2007 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# translate is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# translate; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA

from django.conf import settings
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils.translation import get_language_bidi
from pootle_app.models.profile import get_profile

def get_title():
    return _(settings.TITLE)

def get_description():
    return _(settings.DESCRIPTION)

def localize_links(request):
    """Localize all the generic links"""

    links = {}
    links['home'] = _('Home')
    links['projects'] = _('All projects')
    links['languages'] = _('All languages')
    links['account'] = _('My Account')
    links['admin'] = _('Admin')
    links['doc'] = _('Help')
    links['doclang'] = getdoclang(request.LANGUAGE_CODE)
    links['logout'] = _('Log out')
    links['login'] = _('Log in')
    links['about'] = _('About')
    # l10n: Verb, as in "to register"
    links['register'] = _('Register')
    links['activate'] = _('Activate')
    # accessibility links
    links['skip_nav'] = _('skip to navigation')
    links['switch_language'] = _('switch language')
    return links


def getdoclang(language):
    """Get the language code that the docs should be displayed in."""

    # TODO: Determine the available languages programmatically.
    available_languages = ['en']
    if language in available_languages:
        return language
    else:
        return 'en'


def languagedir():
    """Returns whether the language is right to left"""
    if get_language_bidi():
        return "rtl"
    else:
        return "ltr"


def weblanguage(language):
    """Reformats the language code from locale style (pt_BR) to web
    style (pt-br)"""

    return language.replace('_', '-')


def completetemplatevars(templatevars, request, bannerheight=135):
    """fill out default values for template variables"""

    if not 'instancetitle' in templatevars:
        templatevars['instancetitle'] = get_title()
    templatevars['sessionvars'] = {'status': get_profile(request.user).status,
                                   'isopen': request.user.is_authenticated(),
                                   'issiteadmin': request.user.is_superuser}
    templatevars['request'] = request
    if not 'mediaurl' in templatevars:
        templatevars['mediaurl'] = settings.MEDIA_URL
    if not 'enablealtsrc' in templatevars:
        templatevars['enablealtsrc'] = settings.ENABLE_ALT_SRC
    templatevars['aboutlink'] = _('About this Pootle server')
    templatevars['uilanguage'] = weblanguage(request.LANGUAGE_CODE)
    templatevars['uidir'] = languagedir()
    # TODO FIXME cssaligndir is deprecated?
    if templatevars['uidir'] == 'ltr':
        templatevars['cssaligndir'] = 'left'
    else:
        templatevars['cssaligndir'] = 'right'
    templatevars['username_title'] = _('Username')
    try:
        templatevars['username'] = templatevars['username']
    except:
        templatevars['username'] = ''
    templatevars['password_title'] = _('Password')
    templatevars['login_text'] = _('Log in')
    templatevars['logout_text'] = _('Log out')
    templatevars['register_text'] = _('Register')
    templatevars['canregister'] = settings.CAN_REGISTER
    templatevars['links'] = localize_links(request)
    templatevars['current_url'] = request.path_info
    if '?' in request.path_info:
        templatevars['logout_link'] = request.path_info + '&islogout=1'
    else:
        templatevars['logout_link'] = request.path_info + '?islogout=1'
    if 'user' not in templatevars:
        templatevars['user'] = request.user
    if 'search' not in templatevars:
        templatevars['search'] = None
    templatevars['message'] = escape(request.GET.get('message', ''))



