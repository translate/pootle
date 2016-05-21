# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture
def vfolders():
    from pytest_pootle.factories import VirtualFolderDBFactory

    from django.db import connection
    from django.apps import apps

    from pootle.core.utils.db import set_mysql_collation_for_column

    cursor = connection.cursor()

    # VirtualFolderTreeItem
    set_mysql_collation_for_column(
        apps,
        cursor,
        "virtualfolder.VirtualFolderTreeItem",
        "pootle_path",
        "utf8_bin",
        "varchar(255)")

    # VirtualFolder
    set_mysql_collation_for_column(
        apps,
        cursor,
        "virtualfolder.VirtualFolder",
        "name",
        "utf8_bin",
        "varchar(70)")
    set_mysql_collation_for_column(
        apps,
        cursor,
        "virtualfolder.VirtualFolder",
        "location",
        "utf8_bin",
        "varchar(255)")

    VirtualFolderDBFactory(filter_rules="store0.po")
    VirtualFolderDBFactory(filter_rules="store1.po")
    VirtualFolderDBFactory(
        location='/{LANG}/project0/',
        is_public=False,
        filter_rules="store0.po")
    VirtualFolderDBFactory(
        location='/{LANG}/project0/',
        is_public=False,
        filter_rules="store1.po")
    VirtualFolderDBFactory(
        location='/language0/project0/',
        filter_rules="subdir0/store4.po")
