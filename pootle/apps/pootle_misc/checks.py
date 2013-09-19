#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
#
# This file is part of Pootle.
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

from django.utils.translation import ugettext_lazy as _

from translate.filters.decorators import Category
from translate.filters import checks


category_names = {
    Category.CRITICAL: _("Critical"),
    Category.FUNCTIONAL: _("Functional"),
    Category.COSMETIC: _("Cosmetic"),
    Category.EXTRACTION: _("Extraction"),
    Category.NO_CATEGORY: _("No category"),
}

check_names = {
    'accelerators': _(u"Accelerators"),
    'acronyms': _(u"Acronyms"),
    'blank': _(u"Blank"),
    'brackets': _(u"Brackets"),
    'compendiumconflicts': _(u"Compendium conflict"),
    'credits': _(u"Translator credits"),
    'doublequoting': _(u"Double quotes"),
    'doublespacing': _(u"Double spaces"),
    'doublewords': _(u"Repeated word"),
    'emails': _(u"E-mail"),
    'endpunc': _(u"Ending punctuation"),
    'endwhitespace': _(u"Ending whitespace"),
    'escapes': _(u"Escapes"),
    'filepaths': _(u"File paths"),
    'functions': _(u"Functions"),
    'gconf': _(u"GConf values"),
    'kdecomments': _(u"Old KDE comment"),
    'long': _(u"Long"),
    'musttranslatewords': _(u"Must translate words"),
    'newlines': _(u"Newlines"),
    'nplurals': _(u"Number of plurals"),
    'notranslatewords': _(u"Don't translate words"),
    'numbers': _(u"Numbers"),
    'options': _(u"Options"),
    'printf': _(u"printf()"),
    'puncspacing': _(u"Punctuation spacing"),
    'purepunc': _(u"Pure punctuation"),
    'sentencecount': _(u"Number of sentences"),
    'short': _(u"Short"),
    'simplecaps': _(u"Simple capitalization"),
    'simpleplurals': _(u"Simple plural(s)"),
    'singlequoting': _(u"Single quotes"),
    'startcaps': _(u"Starting capitalization"),
    'startpunc': _(u"Starting punctuation"),
    'startwhitespace': _(u"Starting whitespace"),
    # Translators: This refers to tabulation characters
    'tabs': _(u"Tabs"),
    'unchanged': _(u"Unchanged"),
    'untranslated': _(u"Untranslated"),
    'urls': _(u"URLs"),
    'validchars': _(u"Valid characters"),
    'variables': _(u"Placeholders"),
    'xmltags': _(u"XML tags"),
}

excluded_filters = ['hassuggestion', 'spellcheck']


def get_qualitychecks():
    sc = checks.StandardChecker()
    for filt in sc.defaultfilters:
        if not filt in excluded_filters:
            # don't use an empty string because of
            # http://bugs.python.org/issue18190
            getattr(sc, filt)(u'_', u'_')

    return sc.categories


def get_qualitycheck_schema(path_obj):
    d = {}
    checks = get_qualitychecks()

    for check, cat in checks.items():
        if not cat in d:
            d[cat] = {
                'code': cat,
                'title': u"%s" % category_names[cat],
                'checks': []
            }
        d[cat]['checks'].append({
            'code': check,
            'title': u"%s" %
                     check_names[check] if check in check_names else check,
            'url': path_obj.get_translate_url(check=check)
        })

    result = sorted([item for code, item in d.items()], key=lambda x: x['code'],
                    reverse=True)

    return result


def get_qualitychecks_by_category(category):
    checks = get_qualitychecks()
    return filter(lambda x: checks[x] == category, checks)
