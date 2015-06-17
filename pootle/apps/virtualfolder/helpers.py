#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.url_helpers import get_all_pootle_paths, split_pootle_path
from pootle_app.models import Directory
from pootle_store.models import Store

from .models import VirtualFolder


def extract_vfolder_from_path(pootle_path):
    """Return a valid virtual folder and an adjusted pootle path.

    This accepts a pootle path and extracts the virtual folder from it (if
    present) returning the virtual folder and the clean path.

    If it can't be determined the virtual folder, then the provided path is
    returned unchanged along as a None value.

    The path /gl/firefox/browser/vfolder/chrome/file.po with the vfolder
    virtual folder on it will be converted to
    /gl/firefox/browser/chrome/file.po if the virtual folder exists and is
    public.

    Have in mind that several virtual folders with the same name might apply in
    the same path (as long as they have different locations this is possible)
    and in such cases the one with higher priority is returned.
    """
    lang, proj, dir_path, filename = split_pootle_path(pootle_path)

    if ((filename and Store.objects.filter(pootle_path=pootle_path).exists()) or
        Directory.objects.filter(pootle_path=pootle_path).exists()):
        # If there is no vfolder then return the provided path.
        return None, pootle_path

    # Get the pootle paths for all the parents except the one for the file and
    # those for the translation project and above.
    all_dir_paths = [dir_path for dir_path in get_all_pootle_paths(pootle_path)
                     if dir_path.count('/') > 3 and dir_path.endswith('/')]
    all_dir_paths = sorted(all_dir_paths)

    for dir_path in all_dir_paths:
        if Directory.objects.filter(pootle_path=dir_path).exists():
            continue

        # There is no directory with such path, and that might mean that it
        # includes a virtual folder.
        valid_starting_path, vfolder_name = dir_path.rstrip('/').rsplit('/', 1)

        vfolders = VirtualFolder.objects.filter(
            name=vfolder_name,
            is_public=True
        ).order_by('-priority')

        vfolder = None

        for vf in vfolders:
            # There might be several virtual folders with the same name, so get
            # the first higher priority one that applies to the adjusted path.
            try:
                # Ensure that the virtual folder applies in the path.
                vf.get_adjusted_location(valid_starting_path + '/')
            except Exception:
                continue

            vfolder = vf
            break

        if vfolder is None:
            # The virtual folder does not exist or is not public or doesn't
            # apply in this location, so this is an invalid path.
            break

        valid_ending_path = pootle_path.replace(dir_path, '')
        adjusted_path = '/'.join([valid_starting_path, valid_ending_path])

        return vfolder, adjusted_path

    # There is no virtual folder (or is not public) and the provided path
    # doesn't exist, so let the calling code to deal with this.
    return None, pootle_path
