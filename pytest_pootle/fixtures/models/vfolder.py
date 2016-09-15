# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


VF_RULE_TESTS = [
    "*",
    "store.po",
    "*/subdir0/*"]


@pytest.fixture(params=VF_RULE_TESTS)
def vf_rules(request):
    return request.param


@pytest.fixture
def vfolder0():
    from virtualfolder.models import VirtualFolder

    return VirtualFolder.objects.first()
