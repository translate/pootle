# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.views import PootleJSON


@pytest.mark.django_db
def test_view_pootle_json():
    json_test = PootleJSON()
    ctx = dict(foo="bar")
    assert json_test.get_response_data(ctx) == ctx
