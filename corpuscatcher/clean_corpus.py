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

import os
import re

from gettext import gettext as _


def line_is_valid(good, bad, unsure):
    """Determine if a line with the given numbers are valid."""
    return bad < good + unsure

def clean_file(corpus, remove_bad=False, dividers_regex=r"[^\w'-]"):
    """Clean corpus file by breaking it up into words (according to
        C{dividers_regex}) and testing those words to C{goodfile} and
        C{badfile} if available. L{line_is_valid} then determines if a given
        line (paragraph) is valid according to the creteria defined there.
        """
    global badwords
    global goodwords
    linecount = 0
    textlines = []
    dividers = re.compile(dividers_regex, flags=re.UNICODE)

    for line in corpus.xreadlines():
        cleanline = []
        linecount += 1

        # line represents a paragraph
        if linecount == 1:
            continue # Skip first line (URL)

        good = bad = unsure = 0

        for word in dividers.split(line):
            if not word:
                continue # Skip empty strings
            cword = clean_word(word)

            # Most words should be good, so we test for it first
            if cword.lower() in goodwords:
                good += 1
                cleanline.append(word)
            elif cword.lower() in badwords:
                bad += 1
                if not remove_bad:
                    cleanline.append('__%s__' % (word))
            else:
                unsure += 1
                cleanline.append(word)

        if line_is_valid(good, bad, unsure):
            textlines.append(cleanline)

    return textlines

def clean_word(word, remove_regex=re.compile(r'[_\d]'), replacement=''):
    """Cleans the word of surrounding puncutation and/or decorations."""
    return remove_regex.sub(word, replacement)

def process_file(corpus, remove_bad=False, output_list=False):
    """Cleans the corpus file (C{corpus}) via L{clean_file} and joins the
        resulting list of words appropriate according to C{output_list}.
        """
    words = clean_file(corpus, remove_bad=remove_bad)

    if output_list:
        wordset = set()
        for line in words:
            for word in line:
                wordset.add(word)

        words = list(wordset)
        return words
    else:
        return [' '.join(line) for line in words]



def create_option_parser():
    from optparse import OptionParser
    usage='Usage: %prog [<options>] <file1> [<file2> ...]'
    parser = OptionParser(usage=usage)

    # Word list options
    parser.add_option(
        '-b', '--bad-file',
        dest='badfile',
        default=None,
        help=_('File containing words considered bad (not in the target language).')
    )
    parser.add_option(
        '-g', '--good-file',
        dest='goodfile',
        default=None,
        help=_('File containig words considered good (in the target language).')
    )

    # Word processing options
    parser.add_option(
        '-m', '--mark-bad',
        dest='removebad',
        action='store_false',
        default=True,
        help=_("""Mark any "bad words" found, don't remove them.""")
    )
    parser.add_option(
        '-l', '--list',
        dest='list',
        action='store_true',
        default=False,
        help=_('Print output as a list of words.')
    )

    parser.add_option(
        '-V', '--version',
        dest='ver',
        default=False,
        action='store_true',
        help=_('Display version information and exit.')
    )

    return parser

def main():
    options, args = create_option_parser().parse_args()

    if options.ver:
        from __version__ import print_version_info
        print_version_info('clean_corpus.py')
        exit(0)

    files = []
    for f in args:
        if os.path.exists(f):
            if os.path.isdir(f):
                for fn in os.listdir(f):
                    if fn.endswith('.txt') and not os.path.isdir(fn):
                        files.append(os.path.join(f, fn))
            else:
                files.append(f)

    if not files:
        print 'No input files specified.'
        exit(1)

    global badwords
    global goodwords

    badwords  = options.badfile  and set([w.lower() for w in open(options.badfile).read().split() ]) or set()
    goodwords = options.goodfile and set([w.lower() for w in open(options.goodfile).read().split()]) or set()
    allwords  = []

    for f in files:
        allwords.extend( process_file(open(f), remove_bad=options.removebad, output_list=options.list) )

    allwords = list(set(allwords))
    allwords.sort()

    for word in allwords:
        print word


if __name__ == '__main__':
    main()
