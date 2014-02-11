#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009, 2013 Zuza Software Foundation
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

from pootle.tests import PootleTestCase
from pootle_store.models import Store


class SuggestionTests(PootleTestCase):
    def setUp(self):
        super(SuggestionTests, self).setUp()
        self.store = Store.objects.get(pootle_path="/af/tutorial/pootle.po")

    def test_hash(self):
        unit = self.store.getitem(0)
        suggestion = unit.add_suggestion("gras")
        first_hash = suggestion.target_hash
        suggestion.translator_comment = "my nice comment"
        second_hash = suggestion.target_hash
        assert first_hash != second_hash
        suggestion.target = "gras++"
        assert first_hash != second_hash != suggestion.target_hash
