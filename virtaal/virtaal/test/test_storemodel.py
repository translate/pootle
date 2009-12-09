#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

from virtaal.models import StoreModel

from test_scaffolding import TestScaffolding


class TestStoreModel(TestScaffolding):
    def test_load(self):
        self.model = StoreModel(self.testfile[1], None) # We can pass "None" as the controller, because it does not have an effect on this test
        self.model.load_file(self.testfile[1])
        assert len(self.model) <= len(self.trans_store.units)
        assert self.model.get_filename() == self.testfile[1]
