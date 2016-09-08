# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import search_backend
from pootle.core.plugin import getter

from .models import VirtualFolder
from .search import VFolderDBSearchBackend


@getter(search_backend, sender=VirtualFolder)
def get_vfolder_search_backend(**kwargs_):
    return VFolderDBSearchBackend
