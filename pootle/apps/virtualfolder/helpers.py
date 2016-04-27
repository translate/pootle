# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_app.models import Directory

from .models import VirtualFolderTreeItem


def make_vfolder_treeitem_dict(vfolder_treeitem):
    return {
        'href_all': vfolder_treeitem.get_translate_url(),
        'href_todo': vfolder_treeitem.get_translate_url(
            state='incomplete'),
        'href_sugg': vfolder_treeitem.get_translate_url(
            state='suggestions'),
        'href_critical': vfolder_treeitem.get_critical_url(),
        'title': vfolder_treeitem.vfolder.name,
        'code': vfolder_treeitem.code,
        'priority': vfolder_treeitem.vfolder.priority,
        'is_grayed': not vfolder_treeitem.is_visible,
        'stats': vfolder_treeitem.get_stats(
            include_children=False),
        'icon': 'vfolder'}


def extract_vfolder_from_path(request_path, vfti=None):
    """
    Matches request_path to a VirtualFolderTreeItem pootle_path

    If a match is found, the associated VirtualFolder and Directory.pootle_path
    are returned. Otherwise the original request_path is returned.

    A `VirtualFolderTreeItem` queryset can be passed in for checking for
    Vfolder pootle_paths. This is useful to `select_related` related fields.

    :param request_path: a path that may contain a virtual folder
    :param vfti: optional `VirtualFolderTreeItem` queryset
    :return: (`VirtualFolder`, path)
    """
    if not (request_path.count('/') > 3 and request_path.endswith('/')):
        return None, request_path

    if vfti is None:
        vfti = VirtualFolderTreeItem.objects.all()
    try:
        vfti = vfti.get(pootle_path=request_path)
    except VirtualFolderTreeItem.DoesNotExist:
        return None, request_path
    else:
        return vfti.vfolder, vfti.directory.pootle_path


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
