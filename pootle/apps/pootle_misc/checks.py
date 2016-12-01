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
from translate.filters.decorators import Category, cosmetic, critical
from translate.lang import data

from django.conf import settings

from pootle.i18n.gettext import ugettext_lazy as _

from .util import import_func


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
    'plurr_format': _(u'Plurr format'),
    'plurr_placeholders': _(u'Plurr placeholders'),

    # FIXME: make checks customisable
    'ftl_format': _(u'ftl format'),
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

plurr_format_regex = re.compile(u'{[^{}]*:.*?}')
plurr_placeholders_regex = re.compile(u'{([^{}]*):.*?}|{([^{}]*?)}')
plurr_plural_suffix_regex = re.compile(u'_PLURAL$')


def clean_plurr_placeholder(string):
    return plurr_plural_suffix_regex.sub('', string)


def get_category_id(code):
    return CATEGORY_IDS.get(code)


def get_category_code(cid):
    return CATEGORY_CODES.get(cid)


def get_category_name(code):
    return unicode(CATEGORY_NAMES.get(code))


class SkipCheck(Exception):
    pass


class ENChecker(checks.UnitChecker):

    def run_test(self, test, unit):
        """Runs the given test on the given unit."""
        return test(self.str1, self.str2, language_code=self.language_code)

    def run_filters(self, unit, categorised=False):
        """Make some optimizations before running individual filters in
        `run_test`.
        """
        self.str1 = data.normalized_unicode(unit.source) or u''
        self.str2 = data.normalized_unicode(unit.target) or u''

        self.language_code = unit.store.translation_project.language.code

        return super(ENChecker, self).run_filters(unit, categorised)

    @critical
    def java_format(self, str1, str2, **kwargs):
        return _generic_check(str1, str2, java_format_regex, u"java_format")

    @critical
    def template_format(self, str1, str2, **kwargs):
        return _generic_check(str1, str2, template_format_regex,
                              u"template_format")

    @critical
    def android_format(self, str1, str2, **kwargs):
        return _generic_check(str1, str2, android_format_regex,
                              u"android_format")

    @critical
    def objective_c_format(self, str1, str2, **kwargs):
        return _generic_check(str1, str2, objective_c_format_regex,
                              u"objective_c_format")

    @critical
    def javaencoded_unicode(self, str1, str2, **kwargs):
        return _generic_check(str1, str2, javaencoded_unicode_regex,
                              u"javaencoded_unicode")

    @critical
    def dollar_sign_placeholders(self, str1, str2, **kwargs):
        return _generic_check(str1, str2, dollar_sign_placeholders_regex,
                              u"dollar_sign_placeholders")

    @critical
    def dollar_sign_closure_placeholders(self, str1, str2, **kwargs):
        return _generic_check(str1, str2,
                              dollar_sign_closure_placeholders_regex,
                              u"dollar_sign_closure_placeholders")

    @critical
    def percent_sign_placeholders(self, str1, str2, **kwargs):
        return _generic_check(str1, str2, percent_sign_placeholders_regex,
                              u"percent_sign_placeholders")

    @critical
    def percent_sign_closure_placeholders(self, str1, str2, **kwargs):
        return _generic_check(str1, str2,
                              percent_sign_closure_placeholders_regex,
                              u"percent_sign_closure_placeholders")

    @critical
    def uppercase_placeholders(self, str1, str2, **kwargs):
        # Ignore check for Plurr-formatted strings
        if plurr_format_regex.search(str1):
            return True

        return _generic_check(str1, str2, uppercase_placeholders_regex,
                              u"uppercase_placeholders")

    @critical
    def mustache_placeholders(self, str1, str2, **kwargs):
        # Ignore check for Plurr-formatted strings
        if plurr_format_regex.search(str1):
            return True

        return _generic_check(str1, str2, mustache_placeholders_regex,
                              u"mustache_placeholders")

    @critical
    def percent_brace_placeholders(self, str1, str2, **kwargs):
        return _generic_check(str1, str2, percent_brace_placeholders_regex,
                              u"percent_brace_placeholders")

    @critical
    def mustache_placeholder_pairs(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = mustache_placeholder_pairs_regex.split(string)
            translate = False
            fingerprint = 1

            if is_source:
                if not mustache_placeholder_pairs_open_tag_regex.search(str1):
                    raise SkipCheck()

                return fingerprint

            stack = []
            for chunk in chunks:
                translate = not translate

                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                tag = chunk[3:-2]  # extract 'tagname' from '{{#tagname}}'

                if chunk[2:3] in ['#', '^']:
                    # opening tag
                    # check that all similar tags were closed
                    if tag in stack:
                        fingerprint = 0
                        break
                    stack.append(tag)

                else:
                    # closing tag '{{/tagname}}'
                    if len(stack) == 0 or not stack[-1] == tag:
                        fingerprint = 0
                        break
                    else:
                        stack.pop()

            if len(stack) > 0:
                fingerprint = 0

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"mustache_placeholder_pairs")

    @critical
    def mustache_like_placeholder_pairs(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = mustache_like_placeholder_pairs_regex.split(string)
            translate = False
            fingerprint = 1
            d = {}

            if is_source:
                if mustache_placeholder_pairs_open_tag_regex.search(str1):
                    raise SkipCheck()

                return fingerprint

            for chunk in chunks:
                translate = not translate

                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                if chunk[2:3] != '/':
                    # opening tag
                    tag = chunk[2:-2]
                    if chunk not in d:
                        d[tag] = 1
                    else:
                        d[tag] += 1
                else:
                    # closing tag
                    # extract 'tagname' from '{{/tagname}}'
                    tag = chunk[3:-2]
                    if tag not in d or d[tag] == 0:
                        fingerprint = None
                        break

                    d[tag] -= 1

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"mustache_like_placeholder_pairs")

    @critical
    def date_format(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            is_date_format = bool(date_format_regex.match(string))
            if is_source:
                if not is_date_format:
                    raise SkipCheck()

                # filter out specific English strings which are not dates
                if date_format_exception_regex.match(string):
                    raise SkipCheck()

            return is_date_format

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Incorrect date format")

    @critical
    def whitespace(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = whitespace_regex.split(string)
            translate = False
            fp_data = [u"\001"]

            for chunk in chunks:
                translate = not translate

                # add empty chunk to fingerprint data to detect begin or
                # end whitespaces
                if chunk == u'':
                    fp_data.append(chunk)

                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                fp_data.append(chunk)

            fingerprint = u"\001".join(fp_data)

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Incorrect whitespaces")

    @critical
    def test_check(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            return 0

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Incorrect test check")

    @critical
    def unescaped_ampersands(self, str1, str2, **kwargs):
        if escaped_entities_regex.search(str1):
            chunks = broken_ampersand_regex.split(str2)
            if len(chunks) == 1:
                return True

            raise checks.FilterFailure(u"Unescaped ampersand mismatch")

        return True

    @critical
    def incorrectly_escaped_ampersands(self, str1, str2, **kwargs):
        if escaped_entities_regex.search(str2):
            chunks = broken_ampersand_regex.split(str1)
            if len(chunks) == 1:
                chunks = broken_ampersand_regex.split(str2)
                if len(chunks) == 1:
                    return True

            raise checks.FilterFailure(u"Escaped ampersand mismatch")

        return True

    @critical
    def changed_attributes(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            # hardcoded rule: skip web banner images which are translated
            # differently
            if is_source:
                if img_banner_regex.match(string):
                    raise SkipCheck()

            chunks = changed_attributes_regex.split(string)
            translate = False
            fingerprint = ''
            d = {}
            for chunk in chunks:
                translate = not translate

                if translate:
                    # ordinary text (safe to translate)
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

        raise checks.FilterFailure(u"Changed attributes")

    @critical
    def c_format(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = c_format_regex.split(string)
            translate = False
            fingerprint = ''
            for chunk in chunks:
                translate = not translate

                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                fingerprint += u"\001%s" % chunk

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Incorrect C format")

    @critical
    def non_printable(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = non_printable_regex.split(string)
            translate = False
            fingerprint = ''

            for chunk in chunks:
                translate = not translate
                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                chunk = '{0x%02x}' % ord(chunk)
                fingerprint += u"\001%s" % chunk

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Non printable mismatch")

    @critical
    def unbalanced_tag_braces(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = unbalanced_tag_braces_regex.split(string)
            translate = False
            level = 0

            for chunk in chunks:
                translate = not translate
                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                if level >= 0:
                    if chunk == '<':
                        level += 1

                    if chunk == '>':
                        level -= 1

            return level

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Unbalanced tag braces")

    @critical
    def unbalanced_curly_braces(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = unbalanced_curly_braces_regex.split(string)
            translate = False
            count = 0
            level = 0

            for chunk in chunks:
                translate = not translate
                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                count += 1
                if level >= 0:
                    if chunk == '{':
                        level += 1
                    if chunk == '}':
                        level -= 1

            fingerprint = u"%d\001%d" % (count, level)

            # if source string has unbalanced tags, always report it
            if is_source and not level == 0:
                # just make the fingerprint different by one symbol
                fingerprint += u"\001"

            return fingerprint

        # Ignore check for Plurr-formatted strings
        if plurr_format_regex.search(str1):
            return True

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Unbalanced curly braces")

    @critical
    def tags_differ(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):

            if is_source:
                # hardcoded rule: skip web banner images which are translated
                # differently
                if img_banner_regex.match(string):
                    raise SkipCheck()

                # hardcoded rules for strings that look like tags but are
                # not them
                if no_tags_regex.match(string):
                    raise SkipCheck()

            chunks = tags_differ_regex_0.split(string)
            translate = False
            fingerprint = ''
            d = {}

            for chunk in chunks:
                translate = not translate
                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                mo = tags_differ_regex_1.match(chunk)

                if mo:
                    tag = mo.group(1)
                    if tag in d:
                        d[tag] += 1
                    else:
                        d[tag] = 1

            for key in sorted(d.keys()):
                fingerprint += u"\001%s\001%s" % (key, d[key])

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Tags differ")

    @critical
    def accelerators(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):

            # special rule for banner images in the web client which are
            # translated differently, e.g.:
            # From: <img src="/images/account/bnr_allow.gif"
            #            alt="Allow Account Access" />
            # To:   <h1>Allow Konto Zugriff</h1>
            if is_source:
                if img_banner_regex.match(string):
                    raise SkipCheck()

            # temporarily escape HTML entities
            s = accelerators_regex_0.sub(r'\001\1\001', string)
            chunks = accelerators_regex_1.split(s)
            translate = False
            ampersand_count = 0
            underscore_count = 0
            circumflex_count = 0

            regex = re.compile(u"\001(\w+)\001", re.U)
            for chunk in chunks:
                translate = not translate
                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                if chunk == '&':
                    ampersand_count += 1
                if chunk == '_':
                    underscore_count += 1
                if chunk == '^':
                    circumflex_count += 1

                # restore HTML entities (will return chunks later)
                chunk = regex.sub(r"&\1;", chunk)

            fingerprint = u"%d\001%d\001%d" % (
                ampersand_count, underscore_count, circumflex_count
            )

            return fingerprint

        # Ignore check for Plurr-formatted strings
        if plurr_format_regex.search(str1):
            return True

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Accelerator mismatch")

    @critical
    def broken_entities(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = broken_entities_regex_0.split(string)
            translate = False
            fingerprint = 1

            for chunk in chunks:
                translate = not translate
                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                # check if ';' is present at the end for some known named
                # entities that should never match as false positives in
                # the normal text
                if broken_entities_regex_1.match(chunk):
                    fingerprint += 1

                # check if ';' is present at the end for numeric and
                # hexadecimal entities
                if broken_entities_regex_2.match(chunk):
                    fingerprint += 1

                # check if a prefix '#' symbol is missing for a numeric
                # entity
                if broken_entities_regex_3.match(chunk):
                    fingerprint += 1

                # check if a prefix '#' symbol is missing for a hexadecimal
                # entity
                if broken_entities_regex_4.match(chunk):
                    fingerprint += 1

                # check if a prefix 'x' symbol is missing (or replaced with
                # something else) for a hexadecimal entity
                mo = broken_entities_regex_5.match(chunk)
                if mo:
                    regex = re.compile(u"\D", re.U)
                    if regex.match(mo.group(1)) or regex.match(mo.group(2)):
                        fingerprint += 1

                # the checks below are conservative, i.e. they do not include
                # the full valid Unicode range but just test for common
                # mistakes in real-life XML/HTML entities

                # check if a numbered entity is within acceptable range
                mo = broken_entities_regex_6.match(chunk)
                if mo:
                    number = int(mo.group(1))
                    if number > 65535:
                        fingerprint += 1

                # check if a hexadecimal numbered entity length is within
                # acceptable range
                mo = broken_entities_regex_7.match(chunk)
                if mo:
                    v = int(mo.group(1), 16)
                    if v > 65535:
                        fingerprint += 1

            if is_source and fingerprint > 1:
                fingerprint = u"%d\001" % fingerprint

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Broken HTML entities")

    @critical
    def potential_unwanted_placeholders(self, str1, str2, **kwargs):
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = potential_placeholders_regex.split(string)
            translate = False
            fingerprint = 0

            for chunk_ in chunks:
                translate = not translate
                if translate:
                    # ordinary text (safe to translate)
                    continue

                # placeholder sign
                fingerprint += 1

            return fingerprint

        a_fingerprint = get_fingerprint(str1, True, str2)
        b_fingerprint = get_fingerprint(str2, False, str1)

        if a_fingerprint >= b_fingerprint:
            return True

        raise checks.FilterFailure(u"Potential unwanted placeholders")

    @cosmetic
    def doublequoting(self, str1, str2, **kwargs):
        """Checks whether there is no double quotation mark `"` in source string but
        there is in a translation string.
        """
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = string.split('"')
            if is_source and '"' in string:
                raise SkipCheck()

            translate = False
            double_quote_count = 0

            for chunk_ in chunks:
                translate = not translate
                if translate:
                    # ordinary text (safe to translate)
                    continue

                double_quote_count += 1

            fingerprint = u"%d\001" % double_quote_count

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True

        raise checks.FilterFailure(u"Double quotes mismatch")

    @critical
    def double_quotes_in_tags(self, str1, str2, **kwargs):
        """Checks whether double quotation mark `"` in tags is consistent between the
        two strings.
        """
        def get_fingerprint(string, is_source=False, translation=''):
            chunks = unbalanced_tag_braces_regex.split(string)
            translate = False
            level = 0
            d = {}
            fingerprint = ''
            quotes_paired = True

            for chunk in chunks:
                translate = not translate
                if translate:
                    if level > 0:
                        d[level] += chunk.count('"')
                    continue

                # special text
                if level >= 0:
                    if chunk == '<':
                        level += 1
                        if level not in d:
                            d[level] = 0

                    if chunk == '>':
                        level -= 1

            for key in sorted([x for x in d.keys() if d[x] > 0]):
                fingerprint += u"\001%s\001%s" % (key, d[key])
                quotes_paired &= d[key] % 2 == 0

            return fingerprint, quotes_paired

        # hardcoded rule: skip web banner images which are translated
        # differently
        if img_banner_regex.match(str1):
            return True

        fingerprint1, paired1 = get_fingerprint(str1, is_source=True)
        if paired1:
            fingerprint2, paired2 = get_fingerprint(str2, is_source=False)
            if fingerprint1 == '' and paired2 or fingerprint1 == fingerprint2:
                return True

        raise checks.FilterFailure(u"Double quotes in tags mismatch")

    @critical
    def plurr_format(self, str1, str2, **kwargs):
        """For plurr-formatted strings, checks the syntax is correct."""
        # Ignore check for empty target strings or non Plurr-formatted
        # source strings
        if str2 == u'' or not plurr_format_regex.search(str1):
            return True

        # Ignore check if library is missing
        try:
            from plurr import Plurr
        except ImportError:
            return True

        plurr = Plurr()

        try:
            plurr.format(str2, {}, {
                'locale': kwargs['language_code'],
                'strict': False,
                'callback': lambda x: '',
            })
        except SyntaxError as e:
            raise checks.FilterFailure(e)

        return True

    @critical
    def plurr_placeholders(self, str1, str2, **kwargs):
        """For plurr-formatted strings, checks placeholders used in target
        strings actually exist in the source string.
        """
        if str2 == u'' or not plurr_placeholders_regex.search(str1):
            return True

        placeholders_source = map(
            clean_plurr_placeholder,
            filter(None,
                   reduce(lambda x, y: x + y,
                          map(list, plurr_placeholders_regex.findall(str1)),
                          []))
        )
        placeholders_target = map(
            clean_plurr_placeholder,
            filter(None,
                   reduce(lambda x, y: x + y,
                          map(list, plurr_placeholders_regex.findall(str2)),
                          []))
        )
        if set(placeholders_source) == set(placeholders_target):
            return True

        unknown_in_target = set(placeholders_target) - set(placeholders_source)
        if len(unknown_in_target) > 0:
            raise checks.FilterFailure(
                u'Unknown placeholders in translation: %s' %
                u', '.join(unknown_in_target)
            )

        missing_in_translation = set(placeholders_source) - set(placeholders_target)
        if len(missing_in_translation) > 0:
            raise checks.FilterFailure(
                u'Placeholders missing in translation: %s' %
                u', '.join(missing_in_translation)
            )

        return True


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
        filterfunction = getattr(checker, functionname, None)

        # This filterfunction may only be defined on another checker if
        # using TeeChecker
        if filterfunction is None:
            continue

        filtermessage = filterfunction.__doc__

        try:
            filterresult = checker.run_test(filterfunction, unit)
        except checks.FilterFailure, e:
            filterresult = False
            filtermessage = unicode(e)
        except Exception, e:
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

    if settings.POOTLE_QUALITY_CHECKER:
        checkers = [import_func(settings.POOTLE_QUALITY_CHECKER)()]
    else:
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
