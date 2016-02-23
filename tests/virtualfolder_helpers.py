# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_translationproject.models import TranslationProject
from virtualfolder.helpers import extract_vfolder_from_path
from virtualfolder.models import VirtualFolder, VirtualFolderTreeItem


@pytest.mark.django_db
def test_extract_vfolder_from_path():
    """Tests that vfolder is correctly extracted from path, if any."""
    subdir0 = TranslationProject.objects.get(
        language__code="language1",
        project__code="project1",
    ).directory.child_dirs.first()

    # Check that subdir0 pootle_path matches no vfolder.
    path = subdir0.pootle_path

    assert (None, path) == extract_vfolder_from_path(path)

    # Check that vfoldertreeitem pootle_path returns a vfolder and a clean path.
    vfolder_item = {
        'name': 'vfolder0',
        'location': subdir0.pootle_path,
        'priority': 4,
        'is_public': True,
        'filter_rules': subdir0.child_stores.first().name,
    }
    vfolder0 = VirtualFolder(**vfolder_item)
    vfolder0.save()

    path = subdir0.vf_treeitems.first().pootle_path

    assert (vfolder0, subdir0.pootle_path) == extract_vfolder_from_path(path)

    # Check that the right vfolder is matched and returned.
    subdir1_first_store = subdir0.child_dirs.first().child_stores.first()

    vfolder_location = subdir0.parent.pootle_path
    filter_path = subdir1_first_store.pootle_path.replace(vfolder_location, "")

    vfolder_item.update({
        'location': vfolder_location,
        'priority': 2,
        'filter_rules': filter_path,
    })
    vfolder1 = VirtualFolder(**vfolder_item)
    vfolder1.save()

    path = subdir0.vf_treeitems.first().pootle_path

    assert (vfolder0, subdir0.pootle_path) == extract_vfolder_from_path(path)

    # Despite the virtual folders share the same name they have different
    # locations, but the VirtualFolderTreeItem pootle_path is unique, thus only
    # one exists.
    assert 1 == VirtualFolderTreeItem.objects.filter(pootle_path=path).count()
