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

from pootle_project.models import Project

from ..factories import UserFactory
from ..fixtures.models.permission_set import _require_permission_set
from ..utils import items_equal


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


@pytest.mark.django_db
def test_no_root_hide_permissions(nobody, default, admin, hide, view,
                                  project_foo, project_bar, root):
    """Tests user-accessible projects when there are no `hide` permissions
    set at the root.
    """
    ALL_PROJECTS = [project_foo.code, project_bar.code]

    foo_user = UserFactory.create(username='foo')
    bar_user = UserFactory.create(username='bar')

    # By default everyone has access to projects
    _require_permission_set(default, root, [view])
    _require_permission_set(nobody, root, [view])

    # At the same time, `project_foo` is inaccessible registered users...
    _require_permission_set(default, project_foo.directory,
                            negative_permissions=[hide])

    assert items_equal(Project.accessible_by_user(admin), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(default), [project_bar.code])
    assert items_equal(Project.accessible_by_user(nobody), [project_bar.code])
    assert items_equal(Project.accessible_by_user(foo_user), [project_bar.code])
    assert items_equal(Project.accessible_by_user(bar_user), [project_bar.code])


    # ...and anonymous users as well
    _require_permission_set(nobody, project_foo.directory,
                            negative_permissions=[hide])

    assert items_equal(Project.accessible_by_user(nobody), [project_bar.code])


    # Let's make `project_foo` accessible for `foo_user`
    _require_permission_set(foo_user, project_foo.directory, [view])

    assert items_equal(Project.accessible_by_user(foo_user), ALL_PROJECTS)


    # `project_bar` is now inaccessible for anonymous users
    _require_permission_set(nobody, project_bar.directory,
                            negative_permissions=[hide])

    assert items_equal(Project.accessible_by_user(nobody), [])


@pytest.mark.django_db
def test_root_hide_permissions(nobody, default, admin, hide, view,
                               project_foo, project_bar, root):
    """Tests user-accessible projects when there are `hide` permissions
    set at the root.
    """
    ALL_PROJECTS = [project_foo.code, project_bar.code]

    foo_user = UserFactory.create(username='foo')
    bar_user = UserFactory.create(username='bar')

    # By default all projects are not accessible
    _require_permission_set(default, root, negative_permissions=[hide])
    _require_permission_set(nobody, root, negative_permissions=[hide])

    assert items_equal(Project.accessible_by_user(admin), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(default), [])
    assert items_equal(Project.accessible_by_user(nobody), [])
    assert items_equal(Project.accessible_by_user(foo_user), [])
    assert items_equal(Project.accessible_by_user(bar_user), [])


    # Now let's make `project_foo` accessible to `foo_user`.
    _require_permission_set(foo_user, project_foo.directory, [view])

    assert items_equal(Project.accessible_by_user(admin), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(default), [])
    assert items_equal(Project.accessible_by_user(nobody), [])
    assert items_equal(Project.accessible_by_user(foo_user), [project_foo.code])
    assert items_equal(Project.accessible_by_user(bar_user), [])


    # Making projects accessible for anonymous users should open the door
    # for everyone
    _require_permission_set(nobody, root, [view])

    assert items_equal(Project.accessible_by_user(admin), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(default), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(nobody), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(foo_user), ALL_PROJECTS)
    assert items_equal(Project.accessible_by_user(bar_user), ALL_PROJECTS)
