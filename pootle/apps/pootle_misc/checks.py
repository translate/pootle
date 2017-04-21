# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import re
from collections import OrderedDict

from translate.filters import checks
from translate.filters.decorators import Category
from translate.lang import data

from pootle.i18n.gettext import ugettext_lazy as _


re._MAXCACHE = 2000

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
    Category.NO_CATEGORY: _("Other"),
}

check_names = {
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
    # Evernote checks (excludes duplicates)
    'broken_entities': _(u"Broken HTML Entities"),
    'java_format': _(u"Java format"),
    'template_format': _(u"Template format"),
    'mustache_placeholders': _(u"Mustache placeholders"),
    'mustache_placeholder_pairs': _(u"Mustache placeholder pairs"),
    'mustache_like_placeholder_pairs': _(u"Mustache like placeholder pairs"),
    'c_format': _(u"C format placeholders"),
    'non_printable': _(u"Non printable"),
    'unbalanced_tag_braces': _(u"Unbalanced tag braces"),
    'changed_attributes': _(u"Changed attributes"),
    'unescaped_ampersands': _(u"Unescaped ampersands"),
    'incorrectly_escaped_ampersands': _(u"Incorrectly escaped ampersands"),
    'whitespace': _(u"Whitespaces"),
    'date_format': _(u"Date format"),
    'uppercase_placeholders': _(u"Uppercase placeholders"),
    'percent_sign_placeholders': _(u"Percent sign placeholders"),
    'percent_sign_closure_placeholders':
        _(u"Percent sign closure placeholders"),
    'dollar_sign_placeholders': _(u"$ placeholders"),
    'dollar_sign_closure_placeholders': _(u"$ closure placeholders"),
    'javaencoded_unicode': _(u"Java-encoded unicode"),
    'objective_c_format': _(u"Objective-C format"),
    'android_format': _(u"Android format"),
    'tags_differ': _(u"Tags differ"),
    'unbalanced_curly_braces': _(u"Curly braces"),
    'potential_unwanted_placeholders': _(u"Potential unwanted placeholders"),
    'double_quotes_in_tags': _(u"Double quotes in tags"),
    'percent_brace_placeholders': _(u"Percent brace placeholders"),

    # FIXME: make checks customisable
    'ftl_format': _(u'ftl format'),

    # Romanian-specific checks
    'cedillas': _(u'Romanian: Avoid cedilla diacritics'),
    'niciun_nicio': _(u'Romanian: Use "niciun"/"nicio"'),
}

excluded_filters = ['hassuggestion', 'spellcheck', 'isfuzzy',
                    'isreview', 'untranslated']

# pre-compile all regexps

fmt = u"\{\d+(?:,(?:number|date|time|choice))\}"
fmt_esc = u"\\\{\d+\\\}"
java_format_regex = re.compile(u"(%s|%s)" % (fmt, fmt_esc))

fmt = u"\$\{[a-zA-Z_\d\.\:]+\}"
template_format_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"%\d+\$[a-z]+"
android_format_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"%@|%\d+\$@"
objective_c_format_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"\\\\u[a-fA-F0-9]{4}"
javaencoded_unicode_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"\$[a-zA-Z_\d]+?(?![\$\%])"
dollar_sign_placeholders_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"\$[a-zA-Z_\d]+?\$"
dollar_sign_closure_placeholders_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"\%\%[a-zA-Z_\d]+?\%\%"
percent_sign_closure_placeholders_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"\%[a-zA-Z_]+?(?![\$\%])"
percent_sign_placeholders_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"[A-Z_][A-Z0-9]*_[A-Z0-9_]*(?![a-z])"
uppercase_placeholders_regex = re.compile(u"(%s)" % fmt, re.U)

fmt4 = u"\{{1}\d+,[^\}]+\}{1}"
fmt3 = u"\{{3}\S+?\}{3}"
fmt2 = u"\{{2}\S+?\}{2}"
fmt1 = u"\{{1}\S+?\}{1}"

mustache_placeholders_regex = re.compile(
    u"(%s|%s|%s|%s)" % (fmt4, fmt3, fmt2, fmt1), re.U)

mustache_placeholder_pairs_open_tag_regex = re.compile(
    u"\{{2}[#\^][^\}]+\}{2}", re.U)
fmt = u"\{{2}[#\^\/][^\}]+\}{2}"
mustache_placeholder_pairs_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"\{{2}[\/]?[^\}]+\}{2}"
mustache_like_placeholder_pairs_regex = re.compile(u"(%s)" % fmt, re.U)

# date_format
df_blocks = u"|".join(
    map(lambda x: '%s+' % x, 'GyYMwWDdFEuaHkKhmsSzZX')) + u"|\'[\w]+\'"
df_glued_blocks = u"X+|Z+|\'[\w]*\'"
df_delimiter = u"[^\w']+|\'[\w]*\'"
date_format_regex = re.compile(
    u"^(%(blocks)s)(%(glued_blocks)s)?((%(delimiter)s)+(%(blocks)s))*$" % {
        'blocks': df_blocks,
        'glued_blocks': df_glued_blocks,
        'delimiter': df_delimiter,
    }, re.U)
date_format_exception_regex = re.compile(u"^(M|S|W|F)$", re.I | re.U)

fmt = u"^\s+|\s+$"
whitespace_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"&#\d+;|&[a-zA-Z]+;|&#x[0-9a-fA-F]+;"
escaped_entities_regex = re.compile(u"(%s)" % fmt, re.U)
broken_ampersand_regex = re.compile(u"(&[^#a-zA-Z]+)", re.U)

img_banner_regex = re.compile(u'^\<img src="\/images\/account\/bnr_', re.U)

fmt1 = u"\b(?!alt|placeholder|title)[a-zA-Z_\d]+\s*=\s*'(?:.*?)'"
fmt2 = u'\b(?!alt|placeholder|title)[a-zA-Z_\d]+\s*=\s*"(?:.*?)"'
changed_attributes_regex = re.compile(u"(%s|%s)" % (fmt2, fmt1), re.U)

fmt = u"%[\d]*(?:.\d+)*(?:h|l|I|I32|I64)*[cdiouxefgns]"
c_format_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"[\000-\011\013-\037]"
non_printable_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"[\<\>]"
unbalanced_tag_braces_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"[\{\}]"
unbalanced_curly_braces_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u'^<(Sync Required|None|no attributes|no tags|' + \
    u'no saved|searches|notebook|not available)>$'
no_tags_regex = re.compile(fmt, re.U)

fmt = u"<\/?[a-zA-Z_]+.*?>"
tags_differ_regex_0 = re.compile(u"(%s)" % fmt, re.U)
tags_differ_regex_1 = re.compile(u"<(\/?[a-zA-Z_]+).*?>", re.U)

accelerators_regex_0 = re.compile(u"&(\w+);", re.U)
fmt = u"[&_\^]"
accelerators_regex_1 = re.compile(u"(%s)(?=\w)" % fmt, re.U)

fmt = u"&#?[0-9a-zA-Z]+;?"
broken_entities_regex_0 = re.compile(u"(%s)" % fmt, re.U)
entities = [
    'amp', 'deg', 'frac14', 'frac12', 'frac34', 'lt', 'gt', 'nbsp', 'mdash',
    'ndash', 'hellip', 'laquo', 'raquo', 'ldquo', 'rdquo', 'lsquo', 'rsquo',
    'larr', 'rarr'
]
broken_entities_regex_1 = re.compile(u"^&(%s)$" % '|'.join(entities), re.U)
broken_entities_regex_2 = re.compile(u"^&#x?[0-9a-fA-F]+$", re.U)
broken_entities_regex_3 = re.compile(u"&\d+;", re.U)
broken_entities_regex_4 = re.compile(u"&x[0-9a-fA-F]+;", re.U)
broken_entities_regex_5 = re.compile(u"&#([^x\d])([0-9a-fA-F]+);")
broken_entities_regex_6 = re.compile(u"&#(\d+);")
broken_entities_regex_7 = re.compile(u"&#x([a-zA-Z_]+);", re.U)

fmt = u"[$%_@]"
potential_placeholders_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"\%\{{1}[^\}]+\}{1}"
percent_brace_placeholders_regex = re.compile(u"(%s)" % fmt, re.U)


def get_category_id(code):
    return CATEGORY_IDS.get(code)


def get_category_code(cid):
    return CATEGORY_CODES.get(cid)


def get_category_name(code):
    return unicode(CATEGORY_NAMES.get(code))


class SkipCheck(Exception):
    pass


def run_given_filters(checker, unit, check_names=None):
    """Run all the tests in this suite.

    :rtype: Dictionary
    :return: Content of the dictionary is as follows::

       {'testname': {
           'message': message_or_exception,
           'category': failure_category
        }}

    Do some optimisation by caching some data of the unit for the
    benefit of :meth:`~TranslationChecker.run_test`.
    """
    if check_names is None:
        check_names = []

    checker.str1 = data.normalized_unicode(unit.source) or u""
    checker.str2 = data.normalized_unicode(unit.target) or u""
    checker.language_code = unit.language_code  # XXX: comes from `CheckableUnit`
    checker.hasplural = unit.hasplural()
    checker.locations = unit.getlocations()

    checker.results_cache = {}
    failures = {}

    for functionname in check_names:
        if isinstance(checker, checks.TeeChecker):
            for _checker in checker.checkers:
                filterfunction = getattr(_checker, functionname, None)
                if filterfunction:
                    checker = _checker
                    checker.str1 = data.normalized_unicode(unit.source) or u""
                    checker.str2 = data.normalized_unicode(unit.target) or u""
                    checker.language_code = unit.language_code
                    checker.hasplural = unit.hasplural()
                    checker.locations = unit.getlocations()
                    break
        else:
            filterfunction = getattr(checker, functionname, None)

        # This filterfunction may only be defined on another checker if
        # using TeeChecker
        if filterfunction is None:
            continue

        filtermessage = filterfunction.__doc__

        try:
            filterresult = checker.run_test(filterfunction, unit)
        except checks.FilterFailure as e:
            filterresult = False
            filtermessage = unicode(e)
        except Exception as e:
            if checker.errorhandler is None:
                raise ValueError("error in filter %s: %r, %r, %s" %
                                 (functionname, unit.source, unit.target, e))
            else:
                filterresult = checker.errorhandler(functionname, unit.source,
                                                    unit.target, e)

        if not filterresult:
            # We test some preconditions that aren't actually a cause for
            # failure
            if functionname in checker.defaultfilters:
                failures[functionname] = {
                    'message': filtermessage,
                    'category': checker.categories[functionname],
                }

    checker.results_cache = {}

    return failures


def get_qualitychecks():
    available_checks = {}

    checkers = [checker() for checker in checks.projectcheckers.values()]

    for checker in checkers:
        for filt in checker.defaultfilters:
            if filt not in excluded_filters:
                # don't use an empty string because of
                # http://bugs.python.org/issue18190
                try:
                    getattr(checker, filt)(u'_', u'_')
                except Exception as e:
                    # FIXME there must be a better way to get a list of
                    # available checks.  Some error because we're not actually
                    # using them on real units.
                    logging.error("Problem with check filter '%s': %s",
                                  filt, e)
                    continue

        available_checks.update(checker.categories)

    return available_checks


def get_qualitycheck_schema(path_obj=None):
    d = {}
    checks = get_qualitychecks()

    for check, cat in checks.items():
        if cat not in d:
            d[cat] = {
                'code': cat,
                'name': get_category_code(cat),
                'title': get_category_name(cat),
                'checks': []
            }
        d[cat]['checks'].append({
            'code': check,
            'title': u"%s" % check_names.get(check, check),
            'url': path_obj.get_translate_url(check=check) if path_obj else ''
        })

    result = sorted([item for item in d.values()],
                    key=lambda x: x['code'],
                    reverse=True)

    return result


def get_qualitycheck_list(path_obj):
    """
    Returns list of checks sorted in alphabetical order
    but having critical checks first.
    """
    result = []
    checks = get_qualitychecks()

    for check, cat in checks.items():
        result.append({
            'code': check,
            'is_critical': cat == Category.CRITICAL,
            'title': u"%s" % check_names.get(check, check),
            'url': path_obj.get_translate_url(check=check)
        })

    def alphabetical_critical_first(item):
        critical_first = 0 if item['is_critical'] else 1
        return critical_first, item['title'].lower()

    result = sorted(result, key=alphabetical_critical_first)

    return result


def _generic_check(str1, str2, regex, message):
    def get_fingerprint(string, is_source=False, translation=''):
        chunks = regex.split(string)

        d = {}
        fingerprint = ''

        if is_source and len(chunks) == 1:
            raise SkipCheck()

        for index, chunk in enumerate(chunks):
            # Chunks contain ordinary text in even positions, so they are safe
            # to be skipped.
            if index % 2 == 0:
                continue

            # special text
            if chunk in d:
                d[chunk] += 1
            else:
                d[chunk] = 1

        for key in sorted(d.keys()):
            fingerprint += u"\001%s\001%s" % (key, d[key])

        return fingerprint

    if check_translation(get_fingerprint, str1, str2):
        return True

    raise checks.FilterFailure(message)


def check_translation(get_fingerprint_func, string, translation):
    if translation == '':
        # no real translation provided, skipping
        return True

    try:
        a_fingerprint = get_fingerprint_func(string, is_source=True,
                                             translation=translation)
    except SkipCheck:
        # skip translation as it doesn't match required criteria
        return True

    b_fingerprint = get_fingerprint_func(translation, is_source=False,
                                         translation=string)

    return a_fingerprint == b_fingerprint
