# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import lang_mapper
from pootle.core.plugin import getter

from .lang_mapper import ProjectLanguageMapper
from .models import Project


@getter(lang_mapper, sender=Project)
def get_lang_mapper(**kwargs):
    return ProjectLanguageMapper(kwargs["instance"])
