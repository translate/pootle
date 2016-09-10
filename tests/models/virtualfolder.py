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

from pootle_store.models import Store
from virtualfolder.models import VirtualFolder, VirtualFolderTreeItem


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
def test_vfolder_membership(tp0, store0):
    tp0_stores = ",".join(
        p[len(tp0.pootle_path):]
        for p in tp0.stores.values_list("pootle_path", flat=True))
    vf0 = VirtualFolder.objects.create(
        name="vf0",
        title="the vf0",
        location=tp0.pootle_path,
        filter_rules=store0.name)
    assert vf0.stores.count() == 1
    assert vf0.stores.first() == store0

    vf1 = VirtualFolder.objects.create(
        name="vf1",
        title="the vf1",
        location=tp0.pootle_path,
        filter_rules=tp0_stores)
    assert (
        list(vf1.stores.order_by("pk"))
        == list(tp0.stores.order_by("pk")))
    store_name = vf1.filter_rules.split(",")[0]
    vf1.filter_rules = ",".join(vf1.filter_rules.split(",")[1:])
    store = vf1.stores.get(name=store_name)
    vf1.save()
    assert store not in vf1.stores.all()
    vf1.filter_rules = ",".join([store_name, vf1.filter_rules])
    vf1.save()
    assert store in vf1.stores.all()


@pytest.mark.django_db
def test_vfolder_store_priorities():

    # remove the default vfolders and update units to reset priorities
    VirtualFolder.objects.all().delete()
    [store.save() for store in Store.objects.all()]

    assert all(
        priority == 1
        for priority
        in Store.objects.values_list("priority", flat=True))

    vfolder0 = VirtualFolderDBFactory(filter_rules="store0.po", name="FOO")
    vfolder0.priority = 3
    vfolder0.save()
    vfolder0_stores = vfolder0.stores.values_list("pk", flat=True)
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
    vfolder0_stores = vfolder0.stores.values_list("pk", flat=True)
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
    vfolder1_stores = vfolder1.stores.values_list("pk", flat=True)

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
