# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import site
from pootle.core.plugin import getter

from .site import PootleSite


pootle_site = PootleSite()


@getter(site)
def get_site(**kwargs_):
    return pootle_site
