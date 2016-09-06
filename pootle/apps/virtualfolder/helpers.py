# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.url_helpers import split_pootle_path

from .models import VirtualFolder


def join_pootle_path(lang_code, proj_code, dir_path, filename):
    parts = [lang_code, proj_code]
    if dir_path.strip("/"):
        parts.append(dir_path.strip("/"))
    if filename:
        parts.append(filename)
    else:
        parts.append("")
    return "/".join([""] + parts)


def extract_vfolder_from_path(request_path):
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
    (lang_code, proj_code,
     dir_path, filename) = split_pootle_path(request_path)
    dir_path_parts = dir_path.split("/")
    if not dir_path_parts:
        return None, request_path
    vf_name = dir_path_parts[0]
    try:
        vfolder = VirtualFolder.objects.get(name=vf_name)
    except VirtualFolder.DoesNotExist:
        return None, request_path
    dir_path = "/".join(dir_path_parts[1:])
    tp_path = "/%s%s" % (dir_path, filename)
    if filename:
        if vfolder.path_matcher.path_matches(tp_path):
            return (
                vfolder,
                join_pootle_path(
                    lang_code, proj_code, dir_path, filename))
    elif vfolder.path_matcher.dir_path_matches(tp_path):
        return (
            vfolder,
            join_pootle_path(
                lang_code, proj_code, dir_path, filename))
    return None, request_path
