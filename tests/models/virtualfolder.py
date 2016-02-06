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

from pytest_pootle.factories import VirtualFolderFactory

from pootle_store.models import Unit
from pootle_store.util import OBSOLETE, TRANSLATED


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
def test_vfolder_priority_not_greater_than_zero():
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
        vfolder.clean_fields()

    assert u'Priority must be greater than zero.' in str(excinfo.value)

    # Test zero priority.
    vfolder_item['priority'] = 0
    vfolder = VirtualFolder(**vfolder_item)

    with pytest.raises(ValidationError) as excinfo:
        vfolder.clean_fields()

    assert u'Priority must be greater than zero.' in str(excinfo.value)


@pytest.mark.django_db
def test_vfolder_root_location():
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
        vfolder.clean_fields()

    assert (u'The "/" location is not allowed. Use "/{LANG}/{PROJ}/" instead.'
            in str(excinfo.value))


@pytest.mark.django_db
def test_vfolder_location_starts_with_projects():
    """Tests that the creation of a virtual folder fails if it uses a location
    that starts with /projects/.
    """
    from django.core.exceptions import ValidationError

    from virtualfolder.models import VirtualFolder

    # Test just /projects/ location.
    vfolder_item = {
        'name': "whatever",
        'location': "/projects/",
        'priority': 4,
        'is_public': True,
        'filter_rules': "browser/defines.po",
    }
    vfolder = VirtualFolder(**vfolder_item)

    with pytest.raises(ValidationError) as excinfo:
        vfolder.clean_fields()

    assert (u'Locations starting with "/projects/" are not allowed. Use '
            u'"/{LANG}/" instead.') in str(excinfo.value)

    # Test /projects/tutorial/ location.
    vfolder_item['location'] = "/projects/tutorial/"
    vfolder = VirtualFolder(**vfolder_item)

    with pytest.raises(ValidationError) as excinfo:
        vfolder.clean_fields()

    assert (u'Locations starting with "/projects/" are not allowed. Use '
            u'"/{LANG}/" instead.') in str(excinfo.value)


@pytest.mark.django_db
def test_vfolder_with_no_filter_rules():
    """Tests that the creation of a virtual folder fails if it doesn't have any
    filter rules.
    """
    from django.core.exceptions import ValidationError

    from virtualfolder.models import VirtualFolder

    vfolder_item = {
        'name': "whatever",
        'location': "/af/vfolder_test/",
        'priority': 4,
        'is_public': True,
        'filter_rules': "",
    }
    vfolder = VirtualFolder(**vfolder_item)

    with pytest.raises(ValidationError) as excinfo:
        vfolder.clean_fields()

    assert u'Some filtering rule must be specified.' in str(excinfo.value)


@pytest.mark.django_db
def test_vfolder_membership():

    vfolder = VirtualFolderFactory(filter_rules="store0.po")

    live_units = Unit.objects.filter(state__gt=OBSOLETE)

    expected_units = live_units.filter(store__name="store0.po")

    # check default vfolder membership
    assert (
        sorted(vfolder.units.values_list("pk", flat=True))
        == sorted(expected_units.values_list("pk", flat=True)))

    vfolder.location = "/language0/{PROJ}/"
    vfolder.save()

    expected_units = live_units.filter(
        store__translation_project__language__code="language0",
        store__name="store0.po")

    # check vfolder membership after changing the location
    assert (
        sorted(vfolder.units.values_list("pk", flat=True))
        == sorted(expected_units.values_list("pk", flat=True)))

    obsolete_unit = (
        Unit.objects.filter(
            state=OBSOLETE,
            store__translation_project__language__code="language0",
            store__name="store0.po"))[0]

    # obsolete unit is not in the vfolder
    assert obsolete_unit not in vfolder.units.all()

    obsolete_unit.state = TRANSLATED
    obsolete_unit.save()

    # unobsoleted unit is in the vfolder
    assert obsolete_unit in vfolder.units.all()

    to_obsolete = vfolder.units.all()[0]
    to_obsolete.state = OBSOLETE
    to_obsolete.save()

    # obsoleted unit is not in the vfolder
    assert to_obsolete not in vfolder.units.all()


@pytest.mark.django_db
def test_vfolder_unit_priorities():
    from virtualfolder.models import VirtualFolder

    # remove the default vfolders and update units to reset priorities
    VirtualFolder.objects.all().delete()
    [unit.save() for unit in Unit.objects.all()]

    assert all(
        priority == 1
        for priority
        in Unit.objects.values_list("priority", flat=True))

    vfolder0 = VirtualFolderFactory(filter_rules="store0.po", priority=3)

    assert all(
        priority == 3
        for priority
        in vfolder0.units.values_list("priority", flat=True))

    assert all(
        priority == 1.0
        for priority
        in Unit.objects.filter(vfolders__isnull=True)
                       .values_list("priority", flat=True))

    vfolder0.filter_rules = "store1.po"
    vfolder0.save()

    assert all(
        priority == 3
        for priority
        in vfolder0.units.values_list("priority", flat=True))

    assert all(
        priority == 1.0
        for priority
        in Unit.objects.filter(vfolders__isnull=True)
                       .values_list("priority", flat=True))

    vfolder1 = VirtualFolderFactory(
        location='/{LANG}/project0/',
        filter_rules="store1.po",
        priority=4)
    vf1_pks = vfolder1.units.values_list("pk", flat=True)

    assert all(
        priority == 4.0
        for priority
        in vfolder1.units.values_list("priority", flat=True))

    assert all(
        priority == 3.0
        for priority
        in vfolder0.units.exclude(pk__in=vf1_pks)
                         .values_list("priority", flat=True))

    assert all(
        priority == 1.0
        for priority
        in Unit.objects.filter(vfolders__isnull=True)
                       .values_list("priority", flat=True))
