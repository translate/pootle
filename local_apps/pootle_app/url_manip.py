#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

import urllib

def strip_trailing_slash(path):
    """If path ends with a /, strip it and return the stripped version."""
    if len(path) > 0 and path[-1] == '/':
        return path[:-1]
    else:
        return path

def add_trailing_slash(path):
    """If path does not end with /, add it and return."""
    if len(path) > 0 and path[-1] == '/':
        return path
    else:
        return path + '/'

################################################################################

def clear_path(path):
    """Returns the last item in a URL pattern, clearing the path. For example,
    'chrome/browser/browser.dtd.po' would return 'browser.dtd.po'"""
    path_parts = path.split("/")
    return path_parts[len(path_parts) - 1]

def url_split(path):
    try:
        slash_pos = strip_trailing_slash(path).rindex('/')
        return path[:slash_pos+1], path[slash_pos+1:]
    except ValueError:
        return '', path

def split_trailing_slash(p):
    if p[-1] == u'/':
        return p[:-1], p[-1]
    else:
        return p, u''

def get_relative(ref_path, abs_path):
    def get_last_agreement(ref_chain, abs_chain):
        max_pos = min(len(ref_chain), len(abs_chain))
        for i in xrange(max_pos):
            if ref_chain[i] != abs_chain[i]:
                return i
        return max_pos

    abs_path, abs_slash = split_trailing_slash(abs_path)

    ref_chain = ref_path.split('/')
    ref_chain.pop()

    abs_chain = abs_path.split('/')

    cut_pos = get_last_agreement(ref_chain, abs_chain)
    go_up = (len(ref_chain) - cut_pos) * ['..']
    go_down = abs_chain[cut_pos:]
    result = u'/'.join(go_up + go_down)
    if result == '' and abs_slash != '':
        return './'
    else:
        return result + abs_slash

def parent(url):
    parent_part, _child_part = url_split(url)
    return parent_part

def make_url(url, args={}):
    if len(args) > 0:
        return u'%s?%s' % (url, urllib.urlencode(sorted(args.iteritems())))
    else:
        return url

def basename(url):
    _parent_part, child_part = url_split(url)
    return child_part
