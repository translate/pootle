# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import terminology, terminology_matcher
from pootle.core.plugin import getter
from pootle_store.models import Unit

from .utils import UnitTerminology, UnitTerminologyMatcher


@getter(terminology, sender=Unit)
def get_unit_terminology(**kwargs_):
    return UnitTerminology


@getter(terminology_matcher, sender=Unit)
def get_unit_terminology_matcher(**kwargs_):
    return UnitTerminologyMatcher
