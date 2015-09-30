#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.exceptions import Http400

from pootle_store.views import get_units

from ..utils import create_api_request


@pytest.mark.django_db
def test_get_units(rf, default):
    """Tests units can be retrieved."""
    view = get_units

    # `path` query parameter missing
    request = create_api_request(rf, user=default)
    with pytest.raises(Http400):
        view(request)

    # `path` query parameter present
    request = create_api_request(rf, url='/?path=foo', user=default)
    response = view(request)
    assert response.status_code == 200
