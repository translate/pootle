#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'Pootle.settings'

from pootle_app.core import Directory, Store, iter_stores

def make_model(model, model_list, *args, **kwargs):
    instance = model(*args, **kwargs)
    instance.save()
    model_list.append(instance)
    return instance

class FakeSearch(object):
    def __init__(self):
        self.goal = None

    def matches(self, store):
        return True

def test_iter_stores():
    def setup_directory_tree(models_to_delete):
        foo = make_model(Directory, models_to_delete, parent=Directory.objects.root, name='foo')

        store_a = make_model(Store, models_to_delete, path='/tmp/a', parent=foo, name='store_a')
        store_b = make_model(Store, models_to_delete, path='/tmp/b', parent=foo, name='store_b')
        store_c = make_model(Store, models_to_delete, path='/tmp/c', parent=foo, name='store_c')

        bar = make_model(Directory, models_to_delete, parent=foo, name='bar')

        store_0 = make_model(Store, models_to_delete, path='/tmp/0', parent=bar, name='store_0')
        store_1 = make_model(Store, models_to_delete, path='/tmp/0', parent=bar, name='store_1')
        store_2 = make_model(Store, models_to_delete, path='/tmp/0', parent=bar, name='store_2')

        quux = make_model(Directory, models_to_delete, parent=bar, name='quux')

        store_s = make_model(Store, models_to_delete, path='/tmp/s', parent=quux, name='store_s')
        store_t = make_model(Store, models_to_delete, path='/tmp/t', parent=quux, name='store_t')
        store_u = make_model(Store, models_to_delete, path='/tmp/u', parent=quux, name='store_u')

        baz = make_model(Directory, models_to_delete, parent=foo, name='baz')

        store_x = make_model(Store, models_to_delete, path='/tmp/x', parent=baz, name='store_x')
        store_y = make_model(Store, models_to_delete, path='/tmp/y', parent=baz, name='store_y')
        store_z = make_model(Store, models_to_delete, path='/tmp/z', parent=baz, name='store_z')

        return foo

    def to_unicode(lst):
        return [unicode(item) for item in lst]

    models_to_delete = []
    try:
        search = FakeSearch()
        foo = setup_directory_tree(models_to_delete)

        assert to_unicode(iter_stores(foo, None, search)) == \
            ['store_a', 'store_b', 'store_c', 
             'store_0', 'store_1', 'store_2',
             'store_s', 'store_t', 'store_u',
             'store_x', 'store_y', 'store_z']
        assert to_unicode(iter_stores(foo, ['store_b'], search)) == \
            ['store_b', 'store_c', 
             'store_0', 'store_1', 'store_2',
             'store_s', 'store_t', 'store_u',
             'store_x', 'store_y', 'store_z']
        assert to_unicode(iter_stores(foo, ['bar', 'store_1'], search)) == \
            ['store_1', 'store_2',
             'store_s', 'store_t', 'store_u',
             'store_x', 'store_y', 'store_z']
        assert to_unicode(iter_stores(foo, ['bar', 'quux', 'store_s'], search)) == \
            ['store_s', 'store_t', 'store_u',
             'store_x', 'store_y', 'store_z']
        assert to_unicode(iter_stores(foo, ['bar', 'quux', 'store_u'], search)) == \
            ['store_u',
             'store_x', 'store_y', 'store_z']

        bar = foo.child_dirs.get(name='bar')
        assert to_unicode(iter_stores(bar, None, search)) == \
            ['store_0', 'store_1', 'store_2',
             'store_s', 'store_t', 'store_u']
        assert to_unicode(iter_stores(bar, ['store_0'], search)) == \
            ['store_0', 'store_1', 'store_2',
             'store_s', 'store_t', 'store_u']
        assert to_unicode(iter_stores(bar, ['store_1'], search)) == \
            ['store_1', 'store_2',
             'store_s', 'store_t', 'store_u']
        assert to_unicode(iter_stores(bar, ['quux', 'store_s'], search)) == \
            ['store_s', 'store_t', 'store_u']
        assert to_unicode(iter_stores(bar, ['quux', 'store_t'], search)) == \
            ['store_t', 'store_u']
        assert to_unicode(iter_stores(bar, ['quux', 'store_u'], search)) == \
            ['store_u']

        quux = bar.child_dirs.get(name='quux')
        assert to_unicode(iter_stores(quux, None, search)) == \
            ['store_s', 'store_t', 'store_u']
        assert to_unicode(iter_stores(quux, ['store_s'], search)) == \
            ['store_s', 'store_t', 'store_u']
        assert to_unicode(iter_stores(quux, ['store_t'], search)) == \
            ['store_t', 'store_u']
        assert to_unicode(iter_stores(quux, ['store_u'], search)) == \
            ['store_u']

    finally:
        for model in models_to_delete:
            model.delete()

if __name__ == '__main__':
    test_iter_stores()
