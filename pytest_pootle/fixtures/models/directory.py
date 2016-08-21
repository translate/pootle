# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture(scope="session")
def root():
    """Require the root directory."""
    from pootle_app.models import Directory

    return Directory.objects.root


@pytest.fixture
def subdir0(tp0):
    return tp0.directory.child_dirs.get(name="subdir0")
