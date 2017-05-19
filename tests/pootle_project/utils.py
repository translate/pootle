# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import paths
from pootle_project.utils import ProjectPaths
from pootle_store.models import Store


@pytest.mark.django_db
def test_paths_project_util(project0):
    project_paths = paths.get(project0.__class__)(project0, "1")
    assert isinstance(project_paths, ProjectPaths)
    assert project_paths.context == project0
    assert (
        sorted(project_paths.store_qs.values_list("pk", flat=True))
        == sorted(
            Store.objects.filter(
                translation_project__project=project0).values_list(
                    "pk", flat=True)))
