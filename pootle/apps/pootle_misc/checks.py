#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

from translate.filters.decorators import Category
from translate.filters import checks

from django.utils.translation import ugettext_lazy as _


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
    'isfuzzy': _(u"Fuzzy"),
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
        if filt not in excluded_filters:
            # don't use an empty string because of
            # http://bugs.python.org/issue18190
            getattr(sc, filt)(u'_', u'_')

    return sc.categories


def get_qualitycheck_schema(path_obj=None):
    d = {}
    checks = get_qualitychecks()

    for check, cat in checks.items():
        if cat not in d:
            d[cat] = {
                'code': cat,
                'title': u"%s" % category_names[cat],
                'checks': []
            }
        d[cat]['checks'].append({
            'code': check,
            'title': u"%s" % check_names.get(check, check),
            'url': path_obj.get_translate_url(check=check) if path_obj else ''
        })

    result = sorted([item for code, item in d.items()],
                    key=lambda x: x['code'],
                    reverse=True)

    return result


def get_qualitychecks_by_category(category):
    checks = get_qualitychecks()
    return filter(lambda x: checks[x] == category, checks)


def get_quality_check_failures(path_obj):
    """Returns a list of the failed checks sorted by their importance.

    :param path_obj: A TreeItem instance.
    """
    checks = []

    try:
        property_stats = path_obj.get_checks()
        total = path_obj.get_total_wordcount()
        keys = property_stats.keys()
        keys.sort(reverse=True)

        for i, category in enumerate(keys):
            group = {
                'checks': []
            }

            if category != Category.NO_CATEGORY:
                group.update({
                    'name': category,
                    'display_name': unicode(category_names[category]),
                })

            cat_keys = property_stats[category].keys()
            cat_keys.sort()

            cat_total = 0

            for checkname in cat_keys:
                checkcount = property_stats[category][checkname]
                cat_total += checkcount

                if total and checkcount:
                    check_display = unicode(check_names.get(checkname,
                                                            checkname))
                    check = {
                        'name': checkname,
                        'display_name': check_display,
                        'count': checkcount,
                        'url': path_obj.get_translate_url(check=checkname),
                    }
                    group['checks'].append(check)

            if cat_total:
                checks.append(group)

    except IOError:
        pass

    return checks
