# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from pootle.core.delegate import search_backend
from pootle.core.plugin import getter

from .models import Unit
from .unit.search import DBSearchBackend


@getter(search_backend, sender=Unit)
def get_search_backend(**kwargs):
    return DBSearchBackend
