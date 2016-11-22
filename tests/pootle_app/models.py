# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import revision
from pootle_app.models import Directory


@pytest.mark.django_db
def test_directory_lifecycle_revision(subdir0, tp0, project0, language0):
    target = subdir0.child_dirs.create(name="foo")
    rev = revision.get(Directory)(target)
    # no cache_key on creation
    assert not rev.get(key="stats")
    target.save()
    key = rev.get(key="stats")
    assert key
    assert key == revision.get(Directory)(subdir0).get(key="stats")
    assert key == revision.get(Directory)(tp0.directory).get(key="stats")
    assert key == revision.get(Directory)(tp0.directory.parent).get(key="stats")
    assert key == revision.get(Directory)(language0.directory).get(key="stats")

    target.delete()
    new_key = revision.get(Directory)(subdir0).get(key="stats")
    assert new_key
    assert new_key != key
    assert new_key == revision.get(Directory)(tp0.directory).get(key="stats")
    assert new_key == revision.get(Directory)(tp0.directory.parent).get(key="stats")
    assert new_key == revision.get(Directory)(language0.directory).get(key="stats")
