#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture
def root(transactional_db):
    """Require the root directory."""
    from pootle_app.models import Directory
    root, created = Directory.objects.get_or_create(name='')
    return root


@pytest.fixture
def projects(root):
    """Require the projects directory."""
    from pootle_app.models import Directory
    projects, created = Directory.objects.get_or_create(name='projects',
                                                        parent=root)
    return projects
