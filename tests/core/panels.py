# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.views.panels import Panel


@pytest.mark.django_db
def test_panel_base():
    panel = Panel(None)
    assert panel.get_context_data() == {}
    assert panel.content == ""
