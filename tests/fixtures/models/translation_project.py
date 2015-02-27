#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

import pytest


def _require_tp(language, project):
    """Helper to get/create a new translation project."""
    from pootle_translationproject.models import create_translation_project

    return create_translation_project(language, project)


def _require_disabled_tp(language, project):
    """Helper to get/create a new translation project in disabled state."""
    from pootle_translationproject.models import create_translation_project

    tp = create_translation_project(language, project)
    tp.disabled = True
    tp.save()

    return tp


@pytest.fixture
def afrikaans_tutorial(afrikaans, tutorial):
    """Require Afrikaans Tutorial."""
    return _require_tp(afrikaans, tutorial)


@pytest.fixture
def arabic_tutorial_disabled(arabic, tutorial):
    """Require Arabic Tutorial in disabled state."""
    return _require_disabled_tp(arabic, tutorial)
