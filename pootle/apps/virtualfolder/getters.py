# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import search_backend
from pootle.core.plugin import getter
from pootle_store.models import Store

from .delegate import path_matcher, vfolder_finder
from .models import VirtualFolder
from .search import VFolderDBSearchBackend
from .utils import VirtualFolderFinder, VirtualFolderPathMatcher


@getter(search_backend, sender=VirtualFolder)
def get_vfolder_search_backend(**kwargs_):
    return VFolderDBSearchBackend


@getter(path_matcher, sender=VirtualFolder)
def vf_path_matcher_getter(**kwargs_):
    return VirtualFolderPathMatcher


@getter(vfolder_finder, sender=Store)
def store_vf_finder_getter(**kwargs_):
    return VirtualFolderFinder
