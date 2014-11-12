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

import re
re._MAXCACHE = 2000

from translate.filters.decorators import Category, critical, cosmetic
from translate.filters import checks
from translate.lang import data

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from pootle_misc.util import import_func

category_names = {
    Category.CRITICAL: _("Critical"),
    Category.COSMETIC: _("Cosmetic"),
}


check_names = {
    'accelerators': _(u"Accelerators"),  # fixme duplicated
    'acronyms': _(u"Acronyms"),
    'blank': _(u"Blank"),
    'brackets': _(u"Brackets"),
    'compendiumconflicts': _(u"Compendium conflict"),
    'credits': _(u"Translator credits"),
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
    # Evernote checks
    'broken_entities': _(u"Broken HTML Entities"),
    'java_format': _(u"Java format"),
    'template_format': _(u"Template format"),
    'mustache_placeholders': _(u"Mustache placeholders"),
    'mustache_placeholder_pairs': _(u"Mustache placeholder pairs"),
    'c_format': _(u"C format placeholders"),
    'non_printable': _(u"Non printable"),
    'unbalanced_tag_braces': _(u"Unbalanced tag braces"),
    'changed_attributes': _(u"Changed attributes"),
    'unescaped_ampersands': _(u"Unescaped ampersands"),
    'whitespace': _(u"Whitespaces"),
    'date_format': _(u"Date format"),
    'uppercase_placeholders': _(u"Uppercase placeholders"),
    'percent_sign_placeholders': _(u"Percent sign placeholders"),
    'percent_sign_closure_placeholders': _(u"Percent sign closure placeholders"),
    'dollar_sign_placeholders': _(u"$ placeholders"),
    'dollar_sign_closure_placeholders': _(u"$ closure placeholders"),
    'javaencoded_unicode': _(u"Java-encoded unicode"),
    'objective_c_format': _(u"Objective-C format"),
    'android_format': _(u"Android format"),
    'accelerators': _(u"Accelerators"),
    'tags_differ': _(u"Tags differ"),
    'unbalanced_curly_braces': _(u"Curly braces"),
    'potential_unwanted_placeholders': _(u"Potential unwanted placeholders"),
    'doublequoting': _(u"Double quotes"),
    'double_quotes_in_tags': _(u"Double quotes in tags"),
}

excluded_filters = ['hassuggestion', 'spellcheck']

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

fmt3 = u"\{{3}\S+?\}{3}"
fmt2 = u"\{{2}\S+?\}{2}"
fmt1 = u"\{{1}\S+?\}{1}"
mustache_placeholders_regex = re.compile(u"(%s|%s|%s)" % (fmt3, fmt2, fmt1), re.U)

fmt = u"\{{2}[#\^\/]\S+?\}{2}"
mustache_placeholder_pairs_regex = re.compile(u"(%s)" % fmt, re.U)

date_format_regex_0 = re.compile(u"^([GyMwWDdFEaHkKhmsSzZ]+[^\w]*)+$", re.U)
date_format_regex_1 = re.compile(u"^(Day|Days|May|SMS|M|S|W|F|add)$", re.I|re.U)
date_format_regex_2 = re.compile(u"^(h:mm a|h:mm aa|hh:mm a|hh:mm aa)$", re.U)
date_format_regex_3 = re.compile(u"^(H:mm|HH:mm)$", re.U)
date_format_regex_4 = re.compile(u"^EEEE, MMMM d yyyy, (h:mm a|h:mm aa|hh:mm a|hh:mm aa)$", re.U)
date_format_regex_5 = re.compile(u"^(EEEE, MMMM d yyyy|EEEE, d MMMM yyyy), (H:mm|HH:mm)$", re.U)
date_format_regex_6 = re.compile(u"^MMMM yyyy$", re.U)
date_format_regex_7 = re.compile(u"^yyyy'年'MMMM$", re.U)
date_format_regex_8 = re.compile(u"[^\w]+", re.U)

fmt = u"^\s+|\s+$"
whitespace_regex = re.compile(u"(%s)" % fmt, re.U)

fmt = u"&amp;|&"
unescaped_ampersands_regex = re.compile(u"(%s)" % fmt, re.U)

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
entities = ['amp', 'deg', 'frac14', 'frac12', 'frac34',
    'lt', 'gt', 'nbsp', 'mdash', 'ndash', 'hellip',
    'laquo', 'raquo', 'ldquo', 'rdquo',
    'lsquo', 'rsquo', 'larr', 'rarr'
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


def get_checker(unit):
    checker_class = getattr(settings, 'QUALITY_CHECKER', '')
    if checker_class:
        return import_func(checker_class)()
    else:
        return unit.store.translation_project.checker


class ENChecker(checks.TranslationChecker):

    @critical
    def java_format(self, str1, str2):
        return _generic_check(str1, str2, java_format_regex, u"java_format")

    @critical
    def template_format(self, str1, str2):
        return _generic_check(str1, str2, template_format_regex,
                              u"template_format")

    @critical
    def android_format(self, str1, str2):
        return _generic_check(str1, str2, android_format_regex,
                              u"android_format")

    @critical
    def objective_c_format(self, str1, str2):
        return _generic_check(str1, str2, objective_c_format_regex,
                              u"objective_c_format")

    @critical
    def javaencoded_unicode(self, str1, str2):
        return _generic_check(str1, str2, javaencoded_unicode_regex,
                              u"javaencoded_unicode")

    @critical
    def dollar_sign_placeholders(self, str1, str2):
        return _generic_check(str1, str2, dollar_sign_placeholders_regex,
                              u"dollar_sign_placeholders")

    @critical
    def dollar_sign_closure_placeholders(self, str1, str2):
        return _generic_check(str1, str2, dollar_sign_closure_placeholders_regex,
                              u"dollar_sign_closure_placeholders")

    @critical
    def percent_sign_placeholders(self, str1, str2):
        return _generic_check(str1, str2, percent_sign_placeholders_regex,
                              u"percent_sign_placeholders")

    @critical
    def percent_sign_closure_placeholders(self, str1, str2):
        return _generic_check(str1, str2, percent_sign_closure_placeholders_regex,
                              u"percent_sign_closure_placeholders")

    @critical
    def uppercase_placeholders(self, str1, str2):
        return _generic_check(str1, str2, uppercase_placeholders_regex,
                              u"uppercase_placeholders")

    @critical
    def mustache_placeholders(self, str1, str2):
        return _generic_check(str1, str2, mustache_placeholders_regex,
                              u"mustache_placeholders")

    @critical
    def mustache_placeholder_pairs(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            chunks = mustache_placeholder_pairs_regex.split(str)
            translate = False
            fingerprint = 1
            stack = []
            for chunk in chunks:
                translate = not translate

                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                if not is_source and fingerprint:
                    tag = chunk[3:-2] # extract 'tagname' from '{{#tagname}}'

                    if chunk[2:3] in ['#','^']:
                        # opening tag
                        # check that all similar tags were closed
                        if tag in stack:
                            fingerprint = None
                        stack.append(tag)

                    else:
                        # closing tag
                        if len(stack) == 0 or not stack[-1] == tag:
                            fingerprint = None
                        else:
                            stack.pop()

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True
        else:
            raise checks.FilterFailure(u"mustache_placeholder_pairs")

    @critical
    def date_format(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            if is_source:
                if not date_format_regex_0.match(str):
                    return None

                # filter out specific English strings which are not dates
                if date_format_regex_1.match(str):
                    return None

                # filter out specific translation pairs
                if date_format_regex_2.match(str):
                    if date_format_regex_3.match(translation):
                        return None

                if date_format_regex_4.match(str):
                    if date_format_regex_5.match(translation):
                        return None

                if date_format_regex_6.match(str):
                    if date_format_regex_7.match(translation):
                        return None

            fingerprint = u"\001".join(sorted(date_format_regex_8.split(str)))

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True
        else:
            raise checks.FilterFailure(u"Incorrect date format")

    @critical
    def whitespace(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            chunks = whitespace_regex.split(str)
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
        else:
            raise checks.FilterFailure(u"Incorrect whitespaces")

    @critical
    def test_check(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            return 0

        if check_translation(get_fingerprint, str1, str2):
            return True
        else:
            raise checks.FilterFailure(u"Incorrect test check")

    @critical
    def unescaped_ampersands(self, str1, str2):
        def get_fingerprint(str):
            chunks = unescaped_ampersands_regex.split(str)
            translate = False
            escaped_count = 0
            unescaped_count = 0

            for chunk in chunks:
                translate = not translate

                if translate:
                    # ordinary text (safe to translate)
                    continue

                # special text
                if chunk == '&':
                    unescaped_count += 1
                else:
                    escaped_count += 1

            return escaped_count, unescaped_count

        escaped1, unescaped1 = get_fingerprint(str1)
        if not (escaped1 > 0 and unescaped1 > 0):
            escaped2, unescaped2 = get_fingerprint(str2)
            if not (escaped2 > 0 and unescaped2 > 0):
                if escaped1 == 0:
                    return True
                elif unescaped2 == 0:
                    return True

        raise checks.FilterFailure(u"Unescaped ampersand mismatch")

    @critical
    def changed_attributes(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            # hardcoded rule: skip web banner images which are translated
            # differently
            if is_source:
                if img_banner_regex.match(str):
                    return None

            chunks = changed_attributes_regex.split(str)
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
        else:
            raise checks.FilterFailure(u"Changed attributes")

    @critical
    def c_format(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            chunks = c_format_regex.split(str)
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
        else:
            raise checks.FilterFailure(u"Incorrect C format")

    @critical
    def non_printable(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            chunks = non_printable_regex.split(str)
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
        else:
            raise checks.FilterFailure(u"Non printable mismatch")

    @critical
    def unbalanced_tag_braces(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            chunks = unbalanced_tag_braces_regex.split(str)
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
        else:
            raise checks.FilterFailure(u"Unbalanced tag braces")

    @critical
    def unbalanced_curly_braces(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            chunks = unbalanced_curly_braces_regex.split(str)
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

        if check_translation(get_fingerprint, str1, str2):
            return True
        else:
            raise checks.FilterFailure(u"Unbalanced curly braces")

    @critical
    def tags_differ(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):

            if is_source:
                # hardcoded rule: skip web banner images which are translated
                # differently
                if img_banner_regex.match(str):
                    return None

                # hardcoded rules for strings that look like tags but are
                # not them
                if no_tags_regex.match(str):
                    return None

            chunks = tags_differ_regex_0.split(str)
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
        else:
            raise checks.FilterFailure(u"Tags differ")

    @critical
    def accelerators(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):

            # special rule for banner images in the web client which are
            # translated differently, e.g.:
            # From: <img src="/images/account/bnr_allow.gif"
            #            alt="Allow Account Access" />
            # To:   <h1>Allow Konto Zugriff</h1>
            if is_source:
                if img_banner_regex.match(str):
                    return None

            # temporarily escape HTML entities
            s = accelerators_regex_0.sub(r'\001\1\001', str)
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

        if check_translation(get_fingerprint, str1, str2):
            return True
        else:
            raise checks.FilterFailure(u"Accelerator mismatch")

    @critical
    def broken_entities(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            chunks = broken_entities_regex_0.split(str)
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
                    if regex.match(mo.group(1)) or \
                        regex.match(mo.group(2)):
                        fingerprint += 1

                # the checks below are conservative, i.e. they do not include
                # the full valid Unicode range but just test for common
                # mistakes in real-life XML/HTML entities

                # check if a numbered entity is within acceptable range
                mo = broken_entities_regex_6.match(chunk)
                if mo:
                    number = int(mo.group(1))
                    if (number < 32 and number != 10) or number > 65535:
                        fingerprint += 1

                # check if a hexadecimal numbered entity length is within
                # acceptable range
                mo = broken_entities_regex_7.match(chunk)
                if mo:
                    v = int(mo.group(1), 16)
                    if (v < 32 and v != 10) or v > 65535:
                        fingerprint += 1

            if is_source and fingerprint > 1:
                fingerprint = u"%d\001" % fingerprint

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True
        else:
            raise checks.FilterFailure(u"Broken HTML entities")

    @critical
    def potential_unwanted_placeholders(self, str1, str2):
        def get_fingerprint(str, is_source=False, translation=''):
            chunks = potential_placeholders_regex.split(str)
            translate = False
            fingerprint = 0

            for chunk in chunks:
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
        else:
            raise checks.FilterFailure(u"Potential unwanted placeholders")

    @cosmetic
    def doublequoting(self, str1, str2):
        """Checks whether there is no double quotation mark `"` in source string but
        there is in a translation string.
        """
        def get_fingerprint(str, is_source=False, translation=''):
            chunks = str.split('"')
            if is_source and '"' in str:
                return None

            translate = False
            double_quote_count = 0

            for chunk in chunks:
                translate = not translate
                if translate:
                    # ordinary text (safe to translate)
                    continue

                double_quote_count += 1

            fingerprint = u"%d\001" % double_quote_count

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True
        else:
            raise checks.FilterFailure(u"Double quotes mismatch")

    @critical
    def double_quotes_in_tags(self, str1, str2):
        """Checks whether double quotation mark `"` in tags is consistent between the
-        two strings.
        """
        def get_fingerprint(str, is_source=False, translation=''):
            if is_source:
                # hardcoded rule: skip web banner images which are translated
                # differently
                if img_banner_regex.match(str):
                    return None

            chunks = unbalanced_tag_braces_regex.split(str)
            translate = False
            level = 0
            d = {}
            fingerprint = ''

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

            return fingerprint

        if check_translation(get_fingerprint, str1, str2):
            return True
        else:
            raise checks.FilterFailure(u"Double quotes in tags mismatch")


def run_given_filters(checker, unit, check_names=[]):
    """Run all the tests in this suite.

    :rtype: Dictionary
    :return: Content of the dictionary is as follows::

       {'testname': { 'message': message_or_exception, 'category': failure_category } }

    Do some optimisation by caching some data of the unit for the
    benefit of :meth:`~TranslationChecker.run_test`.
    """
    checker.str1 = data.normalized_unicode(unit.source) or u""
    checker.str2 = data.normalized_unicode(unit.target) or u""
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
                raise ValueError("error in filter %s: %r, %r, %s" % \
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
    sc = ENChecker()
    for filt in sc.defaultfilters:
        if not filt in excluded_filters:
            # don't use an empty string because of
            # http://bugs.python.org/issue18190
            getattr(sc, filt)(u'_', u'_')

    return sc.categories


def get_qualitycheck_schema(path_obj=None):
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


def _generic_check(str1, str2, regex, message):
    def get_fingerprint(str, is_source=False, translation=''):
        chunks = regex.split(str)

        translate = False
        d = {}
        fingerprint = ''

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
    else:
        raise checks.FilterFailure(message)


def check_translation(get_fingerprint_func, string, translation):
    if translation == '':
        # no real translation provided, skipping
        return True

    a_fingerprint = get_fingerprint_func(string, True, translation)

    if a_fingerprint is None:
        # skip translation as it doesn't match required criteria
        return True

    b_fingerprint = get_fingerprint_func(translation, False, string)

    return a_fingerprint == b_fingerprint
