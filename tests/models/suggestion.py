#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009, 2013 Zuza Software Foundation
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

import pytest


@pytest.mark.django_db
def test_hash(af_tutorial_po, system):
    """Tests that target hash changes when suggestion is modified"""
    unit = af_tutorial_po.getitem(0)

    orig_wordcount = unit.store.translated_wordcount
    assert unit.store.suggestion_count == 0
    suggestion = unit.add_suggestion("gras")
    assert unit.store.suggestion_count == 1

    first_hash = suggestion.target_hash
    suggestion.translator_comment = "my nice comment"
    second_hash = suggestion.target_hash
    assert first_hash != second_hash

    suggestion.target = "gras++"
    suggestion.user_id = 1
    assert first_hash != second_hash != suggestion.target_hash

    # FIXME: This breaks everything on MyISAM due to broken transaction expectations
    # unit.accept_suggestion(suggestion, unit.store.translation_project, None)
    # assert unit.store.suggestion_count == 0
    # assert unit.store.translated_wordcount == orig_wordcount + unit.source_wordcount
