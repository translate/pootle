# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_app.models import Directory

from .models import VirtualFolderTreeItem


def vftis_for_child_dirs(directory):
    """
    Returns the vfoldertreeitems for a directory's child directories
    """
    child_dir_pks = [
        child.pk
        for child
        in directory.children
        if isinstance(child, Directory)]
    return VirtualFolderTreeItem.objects.filter(
        directory__pk__in=child_dir_pks)
