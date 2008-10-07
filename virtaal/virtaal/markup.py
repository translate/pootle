#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 Zuza Software Foundation
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

import re


xml_re = re.compile("&lt;[^>]+>")

def fancyspaces(string):
    """Returns the fancy spaces that are easily visible."""
    spaces = string.group()
#    while spaces[0] in "\t\n\r":
#        spaces = spaces[1:]
    return '<span underline="low" foreground="grey"> </span>' * len(spaces)

def markuptext(text, fancyspaces=False, markupescapes=True):
    """Replace special characters &, <, >, add and handle escapes if asked for Pango."""
    if not text:
        return ""
    text = text.replace("&", "&amp;") # Must be done first!
    text = text.replace("<", "&lt;")
    fancy_xml = lambda escape: \
            '<span foreground="darkred">%s</span>' % escape.group()
    text = xml_re.sub(fancy_xml, text)

    if markupescapes:
        fancyescape = lambda escape: \
                '<span foreground="purple">%s</span>' % escape

        text = text.replace("\r\n", fancyescape(r'\r\n') + '\n')
        text = text.replace("\n", fancyescape(r'\n') + '\n')
        text = text.replace("\r", fancyescape(r'\r') + '\n')
        text = text.replace("\t", fancyescape(r'\t'))
    # we don't need it at the end of the string
    if text.endswith("\n"):
        text = text[:-len("\n")]

    if fancyspaces:
        text = addfancyspaces(text)
    return text

def addfancyspaces(text):
    """Insert fancy spaces"""
    #More than two consecutive:
    text = re.sub("[ ]{2,}", fancyspaces, text)
    #At start of string
    text = re.sub("^[ ]+", fancyspaces, text)
    #After newline
    text = re.sub("(?m)\n([ ]+)", fancyspaces, text)
    #At end of string
    text = re.sub("[ ]+$", fancyspaces, text)
    return text

def escape(text):
    """This is to escape text for use with gtk.TextView"""
    if not text:
        return ""
    text = text.replace("\\", '\\\\')
    text = text.replace("\n", '\\n\n')
    text = text.replace("\r", '\\r\n')
    text = text.replace("\\r\n\\n",'\\r\\n')
    text = text.replace("\t", '\\t')
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
