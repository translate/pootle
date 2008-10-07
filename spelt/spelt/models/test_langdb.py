#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Spelt.
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

# Contains LanguageDB: the main model representing a language database and provides access to all its parts.

import os.path
from lxml import etree

from langdb    import LanguageDB
from user      import User
from xml_model import XMLModel

TEST_SAVE = True

class TestLanguageDB(object):
    """Unit test for the LanguageDB class. Test DB is af_test.xldb."""

    def test_load(self):
        ldb = LanguageDB(lang='af')
        ldb.load('test_langdb.xldb')
        assert ldb.filename == 'test_langdb.xldb'

    def test_save(self):
        if not TEST_SAVE:
            return

        ldb = LanguageDB(lang='af')
        ldb.load('test_langdb.xldb')
        ldb.add_user(User('Froodle'))
        ldb.save('test_langdb_save.xldb')
        assert os.path.exists('test_langdb_save.xldb')

    def test_find(self):
        # Find in a section... should return 1 User model
        ldb = LanguageDB(lang='af')
        ldb.load('test_langdb.xldb')
        u2 = ldb.find(id=2, section='users')
        assert isinstance(u2, list)
        assert isinstance(u2[0], User)
        assert u2[0].id == 2

        # Find all models with ID 2
        res = ldb.find(id=2)
        assert isinstance(res, list)
        assert len(res) == 2 # According to test_langdb.xldb
        for m in res:
            assert isinstance(m, XMLModel)

        # Find a user named 'Walter' (me!) with section filtering
        res = ldb.find(section='users', name='Walter')
        assert len(res) == 1
        assert isinstance(res[0], User)
        assert res[0].name == 'Walter'

        # Find a user named 'Walter' (me!) without section filtering
        res = ldb.find(name='Walter')
        assert len(res) == 1
        assert isinstance(res[0], User)
        assert res[0].name == 'Walter'

        # Test OR-ness of find: find 2 models with different keyword searches
        res = ldb.find(user_id=4, source_id=2)
        assert len(res) == 3

        res = ldb.find(value='varkies', status='todo')
        assert len(res) == 2
        assert res[0].value == 'koeie' and res[0].status == 'todo'
        assert res[1].value == 'varkies' and res[1].status == 'todo'
