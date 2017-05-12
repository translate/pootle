# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

from translate.filters.decorators import Category

from pootle.i18n.gettext import ugettext_lazy as _


CATEGORY_IDS = OrderedDict(
    [['critical', Category.CRITICAL],
     ['functional', Category.FUNCTIONAL],
     ['cosmetic', Category.COSMETIC],
     ['extraction', Category.EXTRACTION],
     ['other', Category.NO_CATEGORY]])
CATEGORY_CODES = {v: k for k, v in CATEGORY_IDS.iteritems()}
CATEGORY_NAMES = {
    Category.CRITICAL: _("Critical"),
    Category.COSMETIC: _("Cosmetic"),
    Category.FUNCTIONAL: _("Functional"),
    Category.EXTRACTION: _("Extraction"),
    Category.NO_CATEGORY: _("Other")}

CHECK_NAMES = {
    'accelerators': _(u"Accelerators"),  # fixme duplicated
    'acronyms': _(u"Acronyms"),
    'blank': _(u"Blank"),
    'brackets': _(u"Brackets"),
    'compendiumconflicts': _(u"Compendium conflict"),
    'credits': _(u"Translator credits"),
    'dialogsizes': _(u"Dialog sizes"),
    'doublequoting': _(u"Double quotes"),  # fixme duplicated
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
    'pythonbraceformat': _(u"Python brace placeholders"),
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
    'validxml': _(u"Valid XML"),
    'xmltags': _(u"XML tags"),

    # FIXME: make checks customisable
    'ftl_format': _(u'ftl format'),

    # Romanian-specific checks
    'cedillas': _(u'Romanian: Avoid cedilla diacritics'),
    'niciun_nicio': _(u'Romanian: Use "niciun"/"nicio"')}


EXCLUDED_FILTERS = [
    'hassuggestion',
    'spellcheck',
    'isfuzzy',
    'isreview',
    'untranslated']
