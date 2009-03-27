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

import os
from django.conf import settings
from django.utils.html import escape
from django.utils.translation import ugettext as _
from pootle_app.models.search import Search
from pootle_app.models.profile import get_profile
from pootle_app.models import metadata
from Pootle.i18n.jtoolkit_i18n import nlocalize, tr_lang
from Pootle.i18n import gettext

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
    links['account'] = _('My account')
    links['admin'] = _('Admin')
    links['doc'] = _('Help')
    links['doclang'] = getdoclang(gettext.get_active().language.code)
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


def languagedir(language):
    """Returns whether the language is right to left"""

    shortcode = language[:3]
    if not shortcode.isalpha():
        shortcode = language[:2]
    if shortcode in [
        'ar',
        'arc',
        'dv',
        'fa',
        'he',
        'ks',
        'ps',
        'ur',
        'yi',
        ]:
        return 'rtl'
    return 'ltr'


def weblanguage(language):
    """Reformats the language code from locale style (pt_BR) to web
    style (pt-br)"""

    return language.replace('_', '-')


def localelanguage(language):
    """Reformats the language code from web style (pt-br) to locale
    style (pt_BR)"""

    dashindex = language.find('-')
    if dashindex >= 0:
        language = language[:dashindex] + '_' + language[dashindex + 1:].upper()
    return language


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
    templatevars['uilanguage'] = weblanguage(gettext.get_active().language.code)
    templatevars['uidir'] = languagedir(gettext.get_active().language.code)
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


class PootlePage:
    """the main page"""

    def __init__(self, templatename, templatevars, request, bannerheight=135):
        self.request = request
        self.templatename = templatename
        self.templatevars = templatevars
        self.completevars(bannerheight)

    def completevars(self, bannerheight=135):
        """fill out default values for template variables"""

        if hasattr(self, 'templatevars'):
            completetemplatevars(self.templatevars, self.request,
                                 bannerheight=bannerheight)

    def polarizeitems(self, itemlist):
        """take an item list and alternate the background colour"""

        polarity = False
        for (n, item) in enumerate(itemlist):
            if isinstance(item, dict):
                item['parity'] = ['even', 'odd'][n % 2]
            else:
                item.setpolarity(polarity)
            polarity = not polarity
        return itemlist

    def gettranslationsummarylegendl10n(self):
        """Returns a dictionary of localized headings.  This is only used because
        we can't do L10n directly in our templates. :("""

        headings = {'translated': _('Translations are complete'),
                    'fuzzy': _('Translations need to be checked (they are marked fuzzy)'
                    ), 'untranslated': _('Untranslated')}
        return headings

class PootleNavPage(PootlePage):
    def initpagestats(self):
        """initialise the top level (language/project) stats"""

        self.alltranslated = 0
        self.grandtotal = 0

    def getpagestats(self):
        """return the top level stats"""

        return (self.alltranslated * 100) / max(self.grandtotal, 1)

    def updatepagestats(self, translated, total):
        """updates the top level stats"""

        self.alltranslated += translated
        self.grandtotal += total

    def getstatsheadings(self):
        """returns a dictionary of localised headings"""

        headings = {
            'name': _('Name'),
            'translated': _('Translated'),
            'translatedpercentage': _('Translated percentage'),
            'translatedwords': _('Translated words'),
            'fuzzy': _('Fuzzy'),
            'fuzzypercentage': _('Fuzzy percentage'),
            'fuzzywords': _('Fuzzy words'),
            'untranslated': _('Untranslated'),
            'untranslatedpercentage': _('Untranslated percentage'),
            'untranslatedwords': _('Untranslated words'),
            'total': _('Total'),
            'totalwords': _('Total words'),
            'progress': _('Progress'),
            'summary': _('Summary'),
            }
        return headings

    def getstats(self, project, directory, goal):
        """returns a list with the data items to fill a statistics
        table Remember to update getstatsheadings() above as needed"""

        wanted = ['translated', 'fuzzy', 'total']
        gotten = {}
        stats_totals = metadata.stats_totals(directory, project.checker, Search(goal=goal))
        for key in wanted:
            gotten[key] = stats_totals.get(key, 0)
            wordkey = key + 'sourcewords'
            gotten[wordkey] = stats_totals[wordkey]
        gotten['untranslated'] = (gotten['total'] - gotten['translated'])\
             - gotten['fuzzy']
        gotten['untranslatedsourcewords'] = (gotten['totalsourcewords']
                 - gotten['translatedsourcewords']) - gotten['fuzzysourcewords']
        wanted = ['translated', 'fuzzy', 'untranslated']
        for key in wanted:
            percentkey = key + 'percentage'
            wordkey = key + 'sourcewords'
            gotten[percentkey] = int((gotten[wordkey] * 100)
                                      / max(gotten['totalsourcewords'], 1))
        for key in gotten:
            if key.find('check-') == 0:
                value = gotten.pop(key)
                gotten[key[len('check-'):]] = value
        return gotten

    def getsearchfields(self):
        source = self.request.GET.get('source', '0')
        target = self.request.GET.get('target', '0')
        notes = self.request.GET.get('notes', '0')
        locations = self.request.GET.get('locations', '0')
        tmpfields = [{
            'name': 'source',
            'text': _('Source Text'),
            'value': source,
            'checked': source == '1' and 'checked' or None,
            }, {
            'name': 'target',
            'text': _('Target Text'),
            'value': target,
            'checked': target == '1' and 'checked' or None,
            }, {
            'name': 'notes',
            'text': _('Comments'),
            'value': notes,
            'checked': notes == '1' and 'checked' or None,
            }, {
            'name': 'locations',
            'text': _('Locations'),
            'value': locations,
            'checked': locations == '1' and 'checked' or None,
            }]
        selection = [bool(field['checked']) for field in tmpfields]
        if selection == [True, True, False, False]:
            # use only the default css class for the search form
            self.extra_class = False
        elif selection == [False, False, False, False]:
            # no search field selected - we use the default instead
            tmpfields[0]['checked'] = 'checked'
            tmpfields[1]['checked'] = 'checked'
            self.extra_class = False
        else:
            # add an extra css class to the search form
            self.extra_class = True
        return tmpfields


