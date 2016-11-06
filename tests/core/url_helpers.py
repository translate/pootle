# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.url_helpers import (
    get_editor_filter, split_pootle_path, urljoin)


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


def test_get_editor_filter():
    """Tests editor filters are correctly constructed."""
    assert get_editor_filter(state='untranslated') == '#filter=untranslated'
    assert get_editor_filter(state='untranslated', sort='newest') == \
        '#filter=untranslated&sort=newest'
    assert get_editor_filter(sort='newest') == '#sort=newest'
    assert get_editor_filter(state='all', search='Foo',
                             sfields='locations') == '#filter=all'
    assert get_editor_filter(search='Foo', sfields='locations') == \
        '#search=Foo&sfields=locations'
    assert get_editor_filter(search='Foo', sfields=['locations', 'notes']) == \
        '#search=Foo&sfields=locations,notes'
    assert get_editor_filter(search='Foo: bar.po\nID: 1',
                             sfields='locations') == \
        '#search=Foo%3A+bar.po%0AID%3A+1&sfields=locations'
