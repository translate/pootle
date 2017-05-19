# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import lang_mapper, paths
from pootle.core.plugin import getter

from .lang_mapper import ProjectLanguageMapper
from .models import Project
from .utils import ProjectPaths


@getter(lang_mapper, sender=Project)
def get_lang_mapper(**kwargs):
    return ProjectLanguageMapper(kwargs["instance"])


@getter(paths, sender=Project)
def get_project_paths(**kwargs):
    return ProjectPaths
