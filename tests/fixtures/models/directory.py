#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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


@pytest.fixture
def root(db):
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
