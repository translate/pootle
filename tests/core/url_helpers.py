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

from pootle.core.url_helpers import urljoin


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
