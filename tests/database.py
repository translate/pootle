import pytest
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


@pytest.mark.django_db
def test_backend_db():
    """Ensure that we are always testing sqlite on fast in memory DB"""
    from django.db import connection, connections

    if connection.vendor == "sqlite":
        assert connections.databases["default"]["NAME"] == ":memory:"
