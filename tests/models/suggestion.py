# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import review
from pootle_store.models import Suggestion


@pytest.mark.django_db
def test_hash(store0):
    """Tests that target hash changes when suggestion is modified"""
    unit = store0.units[0]
    suggestions = review.get(Suggestion)()

    suggestion, created_ = suggestions.add(unit, "gras")

    first_hash = suggestion.target_hash
    suggestion.translator_comment = "my nice comment"
    second_hash = suggestion.target_hash
    assert first_hash != second_hash

    suggestion.target = "gras++"
    assert first_hash != second_hash != suggestion.target_hash
