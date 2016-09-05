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

from pootle_store.models import Store, Unit
from virtualfolder.utils import VirtualFolderPathMatcher
from virtualfolder.models import VirtualFolder, VFData


@pytest.mark.django_db
def test_vfolder_directory_clash(project0, language0, subdir0):
    """Tests that the creation of a virtual folder fails if it clashes with
    some already existing directory.

    References #3905.
    """

    vfolder_item = {
        'name': subdir0.name,
        'project': project0,
        'language': language0,
        'priority': 4,
        'is_public': True,
        'filter_rules': subdir0.child_stores.first().name,
    }
    vfolder = VirtualFolder(**vfolder_item)
    with pytest.raises(ValidationError) as excinfo:
        vfolder.save()
    message = u"Problem adding virtual folder '%s'" % subdir0.name
    assert message in excinfo.value.message


@pytest.mark.django_db
def test_vfolder_priority_not_greater_than_zero(project0, language0):
    """Tests that the creation of a virtual folder fails if the provided
    priority is not greater than zero.
    """

    # Test priority less than zero.
    vfolder_item = {
        'name': "whatever",
        'project': project0,
        'language': language0,
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
def test_vfolder_with_no_filter_rules(project0, language0):
    """Tests that the creation of a virtual folder fails if it doesn't have any
    filter rules.
    """

    vfolder_item = {
        'name': "whatever",
        'project': project0,
        'language': language0,
        'priority': 4,
        'is_public': True,
        'filter_rules': "",
    }
    vfolder = VirtualFolder(**vfolder_item)

    with pytest.raises(ValidationError) as excinfo:
        vfolder.clean_fields()

    assert u'Some filtering rule must be specified.' in str(excinfo.value)


@pytest.mark.django_db
def __test_vfolder_unit_priorities():
    # TODO: should priority be a store thing?

    # remove the default vfolders and reset units priorities
    VirtualFolder.objects.all().delete()
    Unit.objects.all().update(priority=1)

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
    name = vf.name
    if vf.language:
        ("%s, language=%s"
         % (name, vf.language.code))
    if vf.project:
        ("%s, project=%s"
         % (name, vf.project.code))
    assert (
        "<VirtualFolder: %s>" % name
        == repr(vf))


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def __test_vfolder_pseudo_membership():
    vf = VirtualFolder.objects.first()
    # data = vf.data_tool.updater.store_data
    vf.data_tool.update()


@pytest.mark.django_db
def test_vfolder_calc_priority(settings, store0):
    vf = VirtualFolderDBFactory(
        filter_rules="/%s" % store0.name)
    vf.priority = 5
    vf.project = store0.translation_project.project
    vf.language = store0.translation_project.language
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
