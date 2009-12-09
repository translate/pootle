#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2009 Zuza Software Foundation
#
# This file is part of Virtaal.
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

from difflib import SequenceMatcher
import re

# We want to draw unexpected spaces specially so that users can spot them
# easily without having to resort to showing all spaces weirdly
_fancy_spaces_re = re.compile(r"""(?m)  #Multiline expression
        [ ]{2,}|     #More than two consecutive
        ^[ ]+|       #At start of a line
        [ ]+$        #At end of line""", re.VERBOSE)
"""A regular expression object to find all unusual spaces we want to show"""

def _fancyspaces(string):
    """Indicate the fancy spaces with a grey squigly."""
    spaces = string.group()
#    while spaces[0] in "\t\n\r":
#        spaces = spaces[1:]
    return u'<span underline="error" foreground="grey">%s</span>' % spaces


# Highligting for XML

_xml_re = re.compile("&lt;[^>]+>")
def _fancy_xml(escape):
    """Marks up the XML to appear dark red."""
    return u'<span foreground="darkred">%s</span>' % escape.group()

def _subtle_escape(escape):
    """Marks up the given escape to appear dark grey without a newline appended."""
    return u'<span foreground="darkgrey">%s</span>' % escape

def _escape_entities(s):
    """Escapes '&' and '<' in literal text so that they are not seen as markup."""
    s = s.replace(u"&", u"&amp;") # Must be done first!
    s = s.replace(u"<", u"&lt;")
    s = _xml_re.sub(_fancy_xml, s)
    return s


# Public methods

def markuptext(text, fancyspaces=True, markupescapes=True, diff_text=""):
    """Markup the given text to be pretty Pango markup.

    Special characters (&, <) are converted, XML markup highligthed with
    escapes and unusual spaces optionally being indicated."""
    if not text:
        return ""


    if diff_text != "":
       text = pango_diff(diff_text, text)
    else:
        text = _escape_entities(text)

    if fancyspaces:
        text = _fancy_spaces_re.sub(_fancyspaces, text)

    if markupescapes:
#        text = text.replace(u"\r\n", _subtle_escape(u'¶\r\n')
        text = text.replace(u"\n", _subtle_escape(u'¶\n'))
        if text.endswith(u'\n</span>'):
            text = text[:-len(u'\n</span>')] + u'</span>'

    return text

def escape(text):
    """This is to escape text for use with gtk.TextView"""
    if not text:
        return ""
    text = text.replace("\n", u'¶\n')
    if text.endswith("\n"):
        text = text[:-len("\n")]
    return text

def unescape(text):
    """This is to unescape text for use with gtk.TextView"""
    if not text:
        return ""
    text = text.replace("\t", "")
    text = text.replace("\n", "")
    text = text.replace("\r", "")
    text = text.replace("\\t", "\t")
    text = text.replace("\\n", "\n")
    text = text.replace("\\r", "\r")
    text = text.replace("\\\\", "\\")
    return text

def pango_diff(a, b):
    """Highlights the differences between a and b for Pango rendering

    The differences are highlighted such that they show what would be required
    to transform a into b."""

    insert_attr = "underline='single' underline_color='#777777' weight='bold' color='#000' background='#a0ffa0'"
    delete_attr = "strikethrough='true' strikethrough_color='#777' color='#000' background='#ccc'"
    replace_attr_remove = delete_attr
    replace_attr_add = "underline='single' underline_color='#777777' weight='bold' color='#000' background='#ffff70'"

    textdiff = ""
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b).get_opcodes():
        if tag == 'equal':
            textdiff += a[i1:i2]
        if tag == "insert":
            textdiff += "<span %(attr)s>%(text)s</span>" % {'attr': insert_attr, 'text': _escape_entities(b[j1:j2])}
        if tag == "delete":
            textdiff += "<span %(attr)s>%(text)s</span>" % {'attr': delete_attr, 'text': _escape_entities(a[i1:i2])}
        if tag == "replace":
            # We don't show text that was removed as part of a change:
            #textdiff += "<span %(attr)s>%(text)s</span>" % {'attr': replace_attr_remove, 'text': _escape_entitiesa(a[i1:i2])}
            textdiff += "<span %(attr)s>%(text)s</span>" % {'attr': replace_attr_add, 'text': _escape_entities(b[j1:j2])}
    return textdiff
