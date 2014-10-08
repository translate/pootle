#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
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

from pootle.core.url_helpers import (urljoin, get_all_pootle_paths,
                                     split_pootle_path)


def test_urljoin():
    """Tests URL parts are properly joined with a base."""
    base = 'https://www.evernote.com/'
    assert urljoin(base) == base
    assert urljoin(base, '/foo/bar', 'baz/blah') == base + 'foo/bar/baz/blah'
    assert urljoin(base, '/foo/', '/bar/', '/baz/') == base + 'foo/bar/baz/'
    assert urljoin(base, '/foo//', '//bar/') == base + 'foo/bar/'
    assert urljoin(base, '/foo//', '//bar/?q=a') == base + 'foo/bar/?q=a'
    assert urljoin(base, 'foo//', '//bar/?q=a') == base + 'foo/bar/?q=a'
    assert urljoin(base, 'foo//////') == base + 'foo/'
    assert urljoin(base, 'foo', 'bar/baz', 'blah') == base + 'foo/bar/baz/blah'
    assert urljoin(base, 'foo/', 'bar', 'baz/') == base + 'foo/bar/baz/'
    assert urljoin('', '', '/////foo') == '/foo'


def test_get_all_pootle_paths():
    """Tests all paths are properly extracted."""
    assert get_all_pootle_paths('') == ['']
    assert get_all_pootle_paths('/') == ['/']
    assert get_all_pootle_paths('/projects/') == ['/projects/']
    assert get_all_pootle_paths('/projects/tutorial/') == \
        ['/projects/tutorial/']
    assert get_all_pootle_paths('/pt/tutorial/') == \
        ['/pt/tutorial/', '/projects/tutorial/']
    assert get_all_pootle_paths('/pt/tutorial/tutorial.po') == \
        ['/pt/tutorial/tutorial.po', '/pt/tutorial/', '/projects/tutorial/']


def test_split_pootle_path():
    """Tests pootle path are properly split."""
    assert split_pootle_path('') == (None, None, '', '')
    assert split_pootle_path('/projects/') == (None, None, '', '')
    assert split_pootle_path('/projects/tutorial/') == \
        (None, 'tutorial', '', '')
    assert split_pootle_path('/pt/tutorial/tutorial.po') == \
        ('pt', 'tutorial', '', 'tutorial.po')
    assert split_pootle_path('/pt/tutorial/foo/tutorial.po') == \
        ('pt', 'tutorial', 'foo/', 'tutorial.po')
