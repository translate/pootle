# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import search_backend
from pootle.core.plugin import getter
from pootle_app.models import Directory
from pootle_store.models import Store

from .delegate import (
    path_matcher, vfolder_finder, vfolders_data_tool, vfolders_data_view)
from .models import VirtualFolder
from .search import VFolderDBSearchBackend
from .utils import (
    DirectoryVFDataTool, VirtualFolderFinder, VirtualFolderPathMatcher)
from .views import VFoldersDataView


@getter(search_backend, sender=VirtualFolder)
def get_vfolder_search_backend(**kwargs_):
    return VFolderDBSearchBackend


@getter(path_matcher, sender=VirtualFolder)
def vf_path_matcher_getter(**kwargs_):
    return VirtualFolderPathMatcher


@getter(vfolder_finder, sender=Store)
def store_vf_finder_getter(**kwargs_):
    return VirtualFolderFinder


@getter(vfolders_data_tool, sender=Directory)
def vf_directory_data_tool_getter(**kwargs_):
    return DirectoryVFDataTool


@getter(vfolders_data_view, sender=Directory)
def vf_directory_data_view_getter(**kwargs_):
    return VFoldersDataView
