#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from __future__ import absolute_import

import pytest


@pytest.mark.django_db
def test_vfolder_directory_clash(af_vfolder_test_browser_defines_po):
    """Tests that the creation of a virtual folder fails if it clashes with
    some already existing directory.

    References #3905.
    """
    from django.core.exceptions import ValidationError

    from virtualfolder.models import VirtualFolder

    vfolder_item = {
        'name': "browser",
        'location': "/af/vfolder_test/",
        'priority': 4,
        'is_public': True,
        'filter_rules': "browser/defines.po",
    }
    vfolder = VirtualFolder(**vfolder_item)

    with pytest.raises(ValidationError) as excinfo:
        vfolder.save()

    assert (u"Problem adding virtual folder 'browser' with location "
            u"'/af/vfolder_test/': VirtualFolderTreeItem clashes with "
            u"Directory /af/vfolder_test/browser/") in str(excinfo.value)


@pytest.mark.django_db
def test_vfolder_priority_not_greater_than_zero(af_vfolder_test_browser_defines_po):
    """Tests that the creation of a virtual folder fails if the provided
    priority is not greater than zero.
    """
    from django.core.exceptions import ValidationError

    from virtualfolder.models import VirtualFolder

    # Test priority less than zero.
    vfolder_item = {
        'name': "whatever",
        'location': "/af/vfolder_test/",
        'priority': -3,
        'is_public': True,
        'filter_rules': "browser/defines.po",
    }
    vfolder = VirtualFolder(**vfolder_item)

    with pytest.raises(ValidationError) as excinfo:
        vfolder.save()

    assert u'Priority must be greater than zero.' in str(excinfo.value)

    # Test zero priority.
    vfolder_item['priority'] = 0
    vfolder = VirtualFolder(**vfolder_item)

    with pytest.raises(ValidationError) as excinfo:
        vfolder.save()

    assert u'Priority must be greater than zero.' in str(excinfo.value)


@pytest.mark.django_db
def test_vfolder_root_location(af_vfolder_test_browser_defines_po):
    """Tests that the creation of a virtual folder fails if it uses location /
    instead of /{LANG}/{PROJ}/.
    """
    from django.core.exceptions import ValidationError

    from virtualfolder.models import VirtualFolder

    vfolder_item = {
        'name': "whatever",
        'location': "/",
        'priority': 4,
        'is_public': True,
        'filter_rules': "browser/defines.po",
    }
    vfolder = VirtualFolder(**vfolder_item)

    with pytest.raises(ValidationError) as excinfo:
        vfolder.save()

    assert (u'The "/" location is not allowed. Use "/{LANG}/{PROJ}/" instead.'
            in str(excinfo.value))
