# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


STATS_DATA = [
    "max_unit_revision",
    "max_unit_mtime",
    "last_submission",
    "last_created_unit",
    "pending_suggestions",
    "total_words",
    "fuzzy_words",
    "translated_words"]


@pytest.fixture
def stats_data_dict(request):
    return STATS_DATA


@pytest.fixture(params=STATS_DATA)
def stats_data_types(request):
    return request.param
