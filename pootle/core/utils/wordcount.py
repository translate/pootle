# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re


re._MAXCACHE = 1000


remove = re.compile(u"[\.]+", re.U)  # dots
delimiters = re.compile(u"[\W]+", re.U)  # anything except a-z, A-Z and _
delimiters_begin = re.compile(u"^[\W]+",
                              re.U)  # anything except a-z, A-Z and _
delimiters_end = re.compile(u"[\W]+$", re.U)  # anything except a-z, A-Z and _

english_date = re.compile(
    u"(^|\W)(January|February|March|April|May|June|July|August|September|"
    u"October|November|December)\s+\d{1,2},\s+(?:\d{2})?\d{2}(\W|$)",
    re.U
)

escaped_xmltag_regex = re.compile(u'(&lt;\/?[\w]+.*?>)', re.U)
xmltag_regex = re.compile(u'(<\/?[\w]+.*?>)', re.U)
java_format_regex = re.compile(u'(\\\{\d+\\\}|\{\d+\})', re.U)
template_format_regex = re.compile(u'(\$\{[\w\.\:]+\})', re.U)
android_format_regex = re.compile(u'(%\d\$\w)', re.U)
sprintf_regex = re.compile(u'(%[\d]*(?:.\d+)*(?:h|l|I|I32|I64)*[cdiouxefgns])',
                           re.U)
objective_c_regex = re.compile(u'(%@)', re.U)
dollar_sign_regex = re.compile(u'(\$[\w\d]+?\$)', re.U)
persent_sign_regex = re.compile(u'(\%[\w\d]+?\%)', re.U)
newline_regex = re.compile(u'(\{\\\n\})', re.U)
escaping_sqc_regex = re.compile(u'(\\\+[rnt])', re.U)
xml_entities_regex = re.compile(u'(&#\d+;|&\w+;)', re.U)
product_names_regex = re.compile(
    u"(Evernote International|Evernote Food|Evernote Hello|Evernote Clearly|"
    u"Evernote Business|Skitch|Evernote®?|Food|^Hello$|Clearly)",
    re.U
)
shortcuts_regex = re.compile(u'(Ctrl\+\w$|Shift\+\w$|Alt\+\w$)', re.U)
shortcuts_modifier_regex = re.compile(u'(Ctrl\+$|Shift\+$|Alt\+$)', re.U)
hanging_symbols_regex = \
    re.compile(u'(^[^\w\&]\s|\s[^\w\&]\s|\s[^\w\&]$|^[^\w\&]$)', re.U)


def find_placeholders(aref, regex, cls=''):
    # regex is compiled re object with pattern surrounded by "()"
    i = 0
    while i < len(aref):
        chunk = aref[i]

        if not chunk['translate']:
            i += 1
        else:
            subchunks = regex.split(chunk['string'])
            a = []
            translate = False

            for subchunk in subchunks:
                translate = not translate
                a.append({
                    'translate': translate,
                    'string': subchunk,
                    'class': cls
                })

            aref[i:i+1] = a
            i += len(a)


def wordcount(string):
    string = re.sub('\n', '{\\n}', string)

    chunks = [{
        'translate': 1,
        'string': u'%s' % string,
    }]

    # FIXME: provide line continuations to fit lines below 80 chars

    # Escaped XML tags (used in some strings)
    find_placeholders(chunks, escaped_xmltag_regex)
    # XML tags
    find_placeholders(chunks, xmltag_regex)
    # Java format and it's escaped version
    find_placeholders(chunks, java_format_regex)
    # Template format
    find_placeholders(chunks, template_format_regex)
    # Android format
    find_placeholders(chunks, android_format_regex)
    # sprintf
    find_placeholders(chunks, sprintf_regex)
    # Objective C style placeholders
    find_placeholders(chunks, objective_c_regex)
    # Dollar sign placeholders
    find_placeholders(chunks, dollar_sign_regex)
    # Percent sign placeholders
    find_placeholders(chunks, persent_sign_regex)
    # '{\n}' newline marker
    find_placeholders(chunks, newline_regex)
    # Escaping sequences (\n, \r, \t)
    find_placeholders(chunks, escaping_sqc_regex)
    # XML entities
    find_placeholders(chunks, xml_entities_regex)
    # Product names
    find_placeholders(chunks, product_names_regex)
    # Shortcuts
    find_placeholders(chunks, shortcuts_regex)
    # Shortcut modifiers
    find_placeholders(chunks, shortcuts_modifier_regex)

    # Find patterns that are not counted as words in Trados
    # Hanging symbols (excluding a-z, _ and &)
    find_placeholders(chunks, hanging_symbols_regex, 'dont-count')

    return _count_words(chunks)


def _count_words(aref):
    # These rules are based on observed Trados 2007 word calculation behavior
    n = 0

    for chunk in aref:
        if chunk['translate']:
            s = chunk['string']
            # Replace the date with just the month name (i.e. count as a single
            # word)
            s = english_date.sub(u'\g<1>\g<2>\g<3>', s)

            s = remove.sub(u'', s)
            s = delimiters_begin.sub(u'', s)
            s = delimiters_end.sub(u'', s)

            a = delimiters.split(s)

            if len(a) > 1 and a[-1] == u'':
                a.pop()

            if len(a) == 1 and a[0] == u'':
                a.pop()

            n += len(a)

    return n
