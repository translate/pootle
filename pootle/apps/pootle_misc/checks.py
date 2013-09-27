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

from translate.filters.decorators import Category

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
    'urls': _(u"URLs"),
    'validchars': _(u"Valid characters"),
    'variables': _(u"Placeholders"),
    'xmltags': _(u"XML tags"),
}


def get_quality_check_failures(path_obj, path_stats, include_url=True):
    """Returns a list of the failed checks sorted by their importance.

    :param path_obj: An object which has the ``getcompletestats`` method.
    :param path_stats: A dictionary of raw stats, as returned by
                       :func:`pootle_misc.stats.get_raw_stats`.
    :param include_url: Whether to include URLs in the returning result
                        or not.
    """
    checks = []

    try:
        property_stats = path_obj.getcompletestats()
        total = path_stats['total']['units']
        keys = property_stats.keys()
        keys.sort(reverse=True)

        for i, category in enumerate(keys):
            checks.append({
                'checks': []
            })

            if category != Category.NO_CATEGORY:
                checks[i].update({
                    'name': category,
                    'display_name': unicode(category_names[category]),
                })

            cat_keys = property_stats[category].keys()
            cat_keys.sort()

            for checkname in cat_keys:
                checkcount = property_stats[category][checkname]

                if total and checkcount:
                    check_display = unicode(check_names.get(checkname,
                                                            checkname))
                    check = {
                        'name': checkname,
                        'display_name': check_display,
                        'count': checkcount
                    }

                    if include_url:
                        check['url'] = path_obj.get_translate_url(
                                check=checkname,
                            )

                    checks[i]['checks'].append(check)
    except IOError:
        pass

    return checks
