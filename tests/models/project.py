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

from ..factories import UserFactory
from ..fixtures.models.permission_set import _require_permission_set
from ..utils import items_equal

from pootle_project.models import Project


@pytest.mark.django_db
def test_no_root_view_permissions(nobody, default, admin, view,
                                  project_foo, project_bar):
    """Tests user-accessible projects when there are no permissions set at
    the root.
    """
    ALL_PROJECTS = [project_foo.code, project_bar.code]

    foo_user = UserFactory.create(username='foo')
    bar_user = UserFactory.create(username='bar')

    # By setting explicit `view` permissions for `foo_user` in
    # `project_foo`, only `foo_user` will be able to access that project
    _require_permission_set(foo_user, project_foo.directory, [view])

    assert items_equal(Project.accessible_by_user(admin), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(foo_user), [project_foo.code])
    assert items_equal(Project.accessible_by_user(bar_user), [])
    assert items_equal(Project.accessible_by_user(default), [])
    assert items_equal(Project.accessible_by_user(nobody), [])


    # Now let's allow showing `project_bar` to all registered users, but
    # keep `project_foo` visible only to `foo_user`.
    _require_permission_set(default, project_bar.directory, [view])

    assert items_equal(Project.accessible_by_user(admin), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(foo_user), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(bar_user), [project_bar.code])
    assert items_equal(Project.accessible_by_user(default), [project_bar.code])
    assert items_equal(Project.accessible_by_user(nobody), [])


@pytest.mark.django_db
def test_root_view_permissions(nobody, default, admin, view,
                               project_foo, project_bar, root):
    """Tests user-accessible projects with view permissions at the root."""
    ALL_PROJECTS = [project_foo.code, project_bar.code]

    foo_user = UserFactory.create(username='foo')
    bar_user = UserFactory.create(username='bar')

    # We'll only give `bar_user` access to all projects server-wide
    _require_permission_set(bar_user, root, [view])

    assert items_equal(Project.accessible_by_user(admin), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(bar_user), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(foo_user), [])
    assert items_equal(Project.accessible_by_user(default), [])
    assert items_equal(Project.accessible_by_user(nobody), [])


    # Now we'll also allow `foo_user` access `project_foo`
    _require_permission_set(foo_user, project_foo.directory, [view])

    assert items_equal(Project.accessible_by_user(foo_user), [project_foo.code])


    # Let's change server-wide defaults: all registered users have access
    # to all projects. `foo_user`, albeit having explicit access for
    # `project_foo`, will be able to access any project because they fall
    # back and extend with the defaults.
    _require_permission_set(default, root, [view])

    assert items_equal(Project.accessible_by_user(admin), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(foo_user), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(bar_user), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(default), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(nobody), [])


    # Let's give anonymous users access to all projects too
    _require_permission_set(nobody, root, [view])

    assert items_equal(Project.accessible_by_user(nobody), ALL_PROJECTS)
