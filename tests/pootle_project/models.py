# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_project.models import Project


@pytest.mark.django_db
def test_project_create_defaults(settings, english):
    foo0 = Project.objects.create(
        code="foo0",
        fullname="Project Foo 0",
        source_language=english)
    assert foo0.config["pootle_fs.fs_type"] == "localfs"
    assert "{POOTLE_TRANSLATION_DIRECTORY}%s" % foo0.code
