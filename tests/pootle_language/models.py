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
from pootle_language.models import Language


@pytest.mark.django_db
def test_languages_revisions():
    initial_revision = revision.get(
        Directory)(Directory.objects.root).get(key="languages")
    new_language = Language.objects.create(code="NEWLANGUAGE")
    new_revision = revision.get(
        Directory)(Directory.objects.root).get(key="languages")
    assert new_revision != initial_revision
    new_language.delete()
    final_revision = revision.get(
        Directory)(Directory.objects.root).get(key="languages")
    assert final_revision != new_revision
