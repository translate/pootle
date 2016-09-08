# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from __future__ import absolute_import

from django.core.exceptions import ValidationError

import pytest

from pytest_pootle.factories import VirtualFolderDBFactory

from pootle_store.constants import OBSOLETE, TRANSLATED
from pootle_store.models import Store, Unit
from virtualfolder.models import VFData, VirtualFolder, VirtualFolderTreeItem
from virtualfolder.utils import VirtualFolderPathMatcher


@pytest.mark.django_db
def test_vfolder_directory_clash(af_vfolder_test_browser_defines_po):
    """Tests that the creation of a virtual folder fails if it clashes with
    some already existing directory.

    References #3905.
    """

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

    vfolder = VirtualFolderDBFactory(filter_rules="store0.po")

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
def test_vfolder_store_priorities():

    # remove the default vfolders and reset units priorities
    VirtualFolder.objects.all().delete()
    [store.save() for store in Store.objects.all()]

    assert all(
        priority == 1
        for priority
        in Store.objects.values_list("priority", flat=True))

    vfolder0 = VirtualFolderDBFactory(filter_rules="store0.po")
    vfolder0.priority = 3
    vfolder0.save()
    vfolder0_stores = vfolder0.units.values_list("store", flat=True).distinct()
    assert all(
        priority == 3
        for priority
        in Store.objects.filter(id__in=vfolder0_stores)
                        .values_list("priority", flat=True))
    assert all(
        priority == 1.0
        for priority
        in Store.objects.exclude(id__in=vfolder0_stores)
                        .values_list("priority", flat=True))

    vfolder0.filter_rules = "store1.po"
    vfolder0.save()
    vfolder0_stores = vfolder0.units.values_list("store", flat=True).distinct()
    assert all(
        priority == 3
        for priority
        in Store.objects.filter(id__in=vfolder0_stores)
                        .values_list("priority", flat=True))
    assert all(
        priority == 1.0
        for priority
        in Store.objects.exclude(id__in=vfolder0_stores)
                        .values_list("priority", flat=True))

    vfolder1 = VirtualFolderDBFactory(
        location='/{LANG}/project0/',
        filter_rules="store1.po")
    vfolder1.priority = 4
    vfolder1.save()
    vfolder1_stores = vfolder1.units.values_list("store", flat=True).distinct()

    assert all(
        priority == 4.0
        for priority
        in Store.objects.filter(id__in=vfolder1_stores)
                        .values_list("priority", flat=True))

    assert all(
        priority == 3.0
        for priority
        in Store.objects.filter(id__in=vfolder0_stores)
                        .exclude(id__in=vfolder1_stores)
                        .values_list("priority", flat=True))

    assert all(
        priority == 1.0
        for priority
        in Store.objects.exclude(id__in=vfolder0_stores)
                        .exclude(id__in=vfolder1_stores)
                        .values_list("priority", flat=True))


@pytest.mark.django_db
def test_virtualfolder_repr():
    vf = VirtualFolderDBFactory(filter_rules="store0.po")
    assert (
        "<VirtualFolder: %s: %s>" % (vf.name, vf.location)
        == repr(vf))


@pytest.mark.django_db
def test_virtualfoldertreeitem_repr():
    vfti = VirtualFolderTreeItem.objects.first()
    assert (
        "<VirtualFolderTreeItem: %s>" % vfti.pootle_path
        == repr(vfti))


@pytest.mark.django_db
def test_vfti_rm():
    original_vftis = VirtualFolderTreeItem.objects.values_list("pk", flat=True)

    vf0 = VirtualFolder.objects.first()
    vf0_vftis = list(vf0.vf_treeitems.values_list("pk", flat=True))

    vf0.delete()
    new_vftis = VirtualFolderTreeItem.objects.values_list("pk", flat=True)
    assert new_vftis

    # Ensure only the other vftis exist.
    assert set(original_vftis) - set(vf0_vftis) == set(new_vftis)

    # Ensure that there are no vftis left when all VirtualFolders have been
    # deleted.
    VirtualFolder.objects.all().delete()
    assert not VirtualFolderTreeItem.objects.exists()


@pytest.mark.django_db
def test_vfolder_calc_priority(settings, store0):
    vf = VirtualFolderDBFactory(
        filter_rules=store0.name)
    vf.priority = 5
    vf.save()
    assert store0.calculate_priority() == 5.0
    settings.INSTALLED_APPS.remove("virtualfolder")
    assert store0.calculate_priority() == 1.0


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_data_repr():
    vf0 = VirtualFolder.objects.first()
    vf_data = VFData.objects.create(vf=vf0)
    assert (
        repr(vf_data)
        == "<VFData: %s>" % vf0)


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_path_matcher(vfolder0):
    assert isinstance(
        vfolder0.path_matcher,
        VirtualFolderPathMatcher)
    assert (
        list(vfolder0.path_matcher.filter_rules)
        == [x.strip() for x in vfolder0.filter_rules.split(",")])
