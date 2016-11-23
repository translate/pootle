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

from pootle_language.models import Language
from pootle_store.models import Store
from virtualfolder.models import VirtualFolder


@pytest.mark.django_db
def test_vfolder_priority_not_greater_than_zero(tp0):
    """Tests that the creation of a virtual folder fails if the provided
    priority is not greater than zero.
    """

    # Test priority less than zero.
    vfolder_item = {
        'name': "whatever",
        'priority': -3,
        'is_public': True,
        'filter_rules': "browser/defines.po",
    }

    with pytest.raises(ValidationError) as excinfo:
        VirtualFolder.objects.create(**vfolder_item)

    assert u'Priority must be greater than zero.' in str(excinfo.value)

    # Test zero priority.
    vfolder_item['priority'] = 1
    vfolder = VirtualFolder.objects.create(**vfolder_item)
    vfolder.priority = 0

    with pytest.raises(ValidationError) as excinfo:
        vfolder.save()

    assert u'Priority must be greater than zero.' in str(excinfo.value)


@pytest.mark.django_db
def test_vfolder_with_no_filter_rules():
    """Tests that the creation of a virtual folder fails if it doesn't have any
    filter rules.
    """

    vfolder_item = {
        'name': "whatever",
        'priority': 4,
        'is_public': True,
        'filter_rules': "",
    }
    with pytest.raises(ValidationError) as excinfo:
        VirtualFolder.objects.create(**vfolder_item)
    assert u'Some filtering rule must be specified.' in str(excinfo.value)

    vfolder_item["filter_rules"] = "FOO"
    vf = VirtualFolder.objects.create(**vfolder_item)
    vf.filter_rules = ""
    with pytest.raises(ValidationError) as excinfo:
        vf.save()
    assert u'Some filtering rule must be specified.' in str(excinfo.value)


@pytest.mark.django_db
def test_vfolder_membership(tp0, store0):
    tp0_stores = ",".join(
        p[len(tp0.pootle_path):]
        for p in tp0.stores.values_list("pootle_path", flat=True))
    vf0 = VirtualFolder.objects.create(
        name="vf0",
        title="the vf0",
        filter_rules=store0.name)
    vf0.projects.add(tp0.project)
    vf0.languages.add(tp0.language)
    vf0.save()
    assert vf0.stores.count() == 1
    assert vf0.stores.first() == store0

    vf1 = VirtualFolder.objects.create(
        name="vf1",
        title="the vf1",
        filter_rules=tp0_stores)
    vf1.projects.add(tp0.project)
    vf1.languages.add(tp0.language)
    vf1.save()
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


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_store_priorities(project0):

    # remove the default vfolders and update units to reset priorities
    VirtualFolder.objects.all().delete()
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
        filter_rules="store1.po")
    vfolder1.languages.add(*Language.objects.all())
    vfolder1.projects.add(project0)
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
        "<VirtualFolder: %s>" % (vf.name)
        == repr(vf))


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_calc_priority(settings, store0):
    vf = store0.vfolders.first()
    vf.priority = 5
    vf.save()
    assert store0.calculate_priority() == 5.0
    settings.INSTALLED_APPS.remove("virtualfolder")
    assert store0.calculate_priority() == 1.0
    settings.INSTALLED_APPS.append("virtualfolder")


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_membership_new_store(tp0):
    vf0 = VirtualFolder.objects.create(
        name="vf0",
        title="the vf0",
        priority=7.0,
        all_languages=True,
        all_projects=True,
        filter_rules="wierd.po")
    wierd_store = Store.objects.create(
        parent=tp0.directory,
        translation_project=tp0,
        name="wierd.po")
    wierd_store.set_priority()
    assert wierd_store in vf0.stores.all()
    assert Store.objects.get(pk=wierd_store.pk).priority == 7
    normal_store = Store.objects.create(
        parent=tp0.directory,
        translation_project=tp0,
        name="normal.po")
    assert normal_store not in vf0.stores.all()
    assert Store.objects.get(pk=normal_store.pk).priority == 1.0
    vf0.delete()
    assert Store.objects.get(pk=wierd_store.pk).priority == 1.0
