# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import data_tool, data_updater
from pootle.core.plugin import getter
from pootle_app.models import Directory
from pootle_language.models import Language

from .delegate import path_matcher, vfolders_data_tool
from .models import VirtualFolder
from .utils import (
    DirectoryVirtualFoldersDataTool, LanguageVirtualFoldersDataTool,
    VirtualFolderDataTool, VirtualFolderDataUpdater, VirtualFolderPathMatcher)


@getter(data_tool, sender=VirtualFolder)
def vf_data_tool_getter(**kwargs_):
    return VirtualFolderDataTool


@getter(data_updater, sender=VirtualFolderDataTool)
def vf_data_tool_updater_getter(**kwargs_):
    return VirtualFolderDataUpdater


@getter(path_matcher, sender=VirtualFolder)
def vf_path_matcher_getter(**kwargs_):
    return VirtualFolderPathMatcher


@getter(vfolders_data_tool, sender=Directory)
def vf_directory_data_tool_getter(**kwargs_):
    return DirectoryVirtualFoldersDataTool


@getter(vfolders_data_tool, sender=Language)
def vf_language_data_tool_getter(**kwargs_):
    return LanguageVirtualFoldersDataTool
