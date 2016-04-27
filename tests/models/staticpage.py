# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from staticpages.models import StaticPage


@pytest.mark.django_db
def test_staticpage_repr():
    staticpage = StaticPage.objects.first()
    assert (
        "<StaticPage: %s>" % staticpage.virtual_path
        == repr(staticpage))
