# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import paths, tp_tool
from pootle.core.plugin import getter
from pootle_project.models import Project

from .models import TranslationProject
from .utils import TPPaths, TPTool


@getter(paths, sender=TranslationProject)
def tp_paths_getter(**kwargs_):
    return TPPaths


@getter(tp_tool, sender=Project)
def tp_tool_getter(**kwargs_):
    return TPTool
