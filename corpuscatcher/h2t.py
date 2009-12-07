#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of CorpusCatcher.
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

"""This file contains functions for extracting text from HTML."""
import codecs, formatter, htmlentitydefs, htmllib
import os, re, sys
from gettext import gettext as _
from StringIO import StringIO

MAXCOL = 10000 # The max number of columns for output text

def apply_htmlparser(html, maxcol=MAXCOL, codec='utf8'):
    """This function extracts from the HTML string by passing it through a
        htmllib.HTMLParser instance (slightly modified for Unicode support).

        Adapted from http://www.bazza.com/~eaganj/weblog/2006/04/04/printing-html-as-text-in-python-with-unicode/

        @type  html: unicode
        @param html: The HTML to extract text from (eg. u"<html><body><h1>Hello</h1>...")
        @type  maxcol: int
        @param maxcol: The maxcol value to passed to formatter.DumbWriter()
        @type  codec: str (passed to codecs.lookup())
        @param codec: The codec to use to parse the HTML.

        @rtype : str
        @return: The text parsed from the HTML."""

    class UnicodeHTMLParser(htmllib.HTMLParser):
        """HTMLParser that can handle unicode charrefs"""

        entitydefs = dict([ (k, unichr(v)) for k, v in htmlentitydefs.name2codepoint.items() ])

        def handle_charref(self, name):
            """Override builtin version to return unicode instead of binary strings for 8-bit chars."""
            try:
                n = int(name)
            except ValueError:
                self.unknown_charref(name)
                return
            if not 0 <= n <= 255:
                self.unknown_charref(name)
                return
            if 0 <= n <= 127:
                self.handle_data(chr(n))
            else:
                self.handle_data(unichr(n))

    sio = StringIO()
    encoder, decoder, reader, writer = codecs.lookup(codec)
    codecio = codecs.StreamReaderWriter(sio, reader, writer, 'replace')
    writer = formatter.DumbWriter(codecio, maxcol)
    prettifier = formatter.AbstractFormatter(writer)

    parser = UnicodeHTMLParser(prettifier)
    parser.feed(html)
    parser.close()

    codecio.seek(0)
    result = codecio.read()
    sio.close()
    codecio.close()

    return result

def remove_by_pattern(text, pattern):
    """Removes the given regex (pattern) from text."""
    junkregex = re.compile(pattern)
    return junkregex.sub('', text)

def remove_tags(text, tags=['script', 'style']):
    """Removes the HTML/XML tags listed in tags from text."""
    tags_str = '|'.join(tags)
    tag_regex = re.compile('<(%s).*?/\\1>' % (tags_str), re.DOTALL)
    return tag_regex.sub(r'<\1></\1>', text)

def html2text(html, rtags=['script', 'style'], maxcol=MAXCOL):
    """Removes specified tags from html, parses the text out of the result and
        then removes "[2134]" and "(image)"-type strings from the that result."""
    if not isinstance(html, basestring):
        if not hasattr(html, 'read'):
            raise ValueError(_('Argument "html" must be a string or file-like object. Got "%s"') % (type(html)))
        html = html.read()

    html = remove_tags(html, tags=rtags)

    import encodings
    try_codecs = ('utf8', 'latin1')
    text = ''
    success = False
    for c in try_codecs:
        try:
            text = apply_htmlparser(html, codec=c)
            success = True
            break
        except UnicodeDecodeError:
            pass

    if not success:
        raise Exception('Unable to determine file encoding.')

    text = remove_by_pattern(text, r'\[\d+\]|\(image\)|(\s+)?\-{3,}(\s+)?')

    return text

if __name__ == '__main__':
    f = os.sys.stdin

    if len(sys.argv) == 2:
        if os.path.exists(sys.argv[1]):
            f = codecs.open(sys.argv[1], 'r')
        else:
            print 'Usage: %s [<input.html>]'
            exit(1)

    print html2text(f.read())
