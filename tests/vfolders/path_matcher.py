# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_fs.utils import PathFilter
from pootle_store.models import Store
from virtualfolder.models import VirtualFolder
from virtualfolder.utils import VirtualFolderPathMatcher


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_path_matcher():
    vfolder = VirtualFolder.objects.create(
        name="avfolder",
        filter_rules="FOO,BAR")
    path_matcher = VirtualFolderPathMatcher(vfolder)
    assert path_matcher.vf == vfolder
    assert path_matcher.tp_path == "/[^/]*/[^/]*/"
    assert isinstance(
        vfolder.path_matcher,
        VirtualFolderPathMatcher)
    # no projects/languages set by default
    assert (
        list(vfolder.path_matcher.languages)
        == list(vfolder.path_matcher.projects)
        == list(vfolder.path_matcher.existing_stores)
        == [])


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_path_matcher_languages(language0, language1):
    vfolder = VirtualFolder.objects.create(
        name="avfolder",
        filter_rules="FOO,BAR")
    vfolder.languages.add(language0)
    vfolder.languages.add(language1)
    # no projects set so no stores
    assert list(vfolder.path_matcher.existing_stores) == []
    assert (
        sorted(vfolder.path_matcher.languages)
        == [language0.pk, language1.pk])
    vfolder.all_languages = True
    vfolder.save()
    assert vfolder.path_matcher.languages is None
    assert list(vfolder.path_matcher.projects) == []
    # no projects set so no stores
    assert list(vfolder.path_matcher.existing_stores) == []
    # didnt forget lang preferences
    vfolder.all_languages = False
    vfolder.save()
    assert (
        sorted(vfolder.path_matcher.languages.values_list("code", flat=True))
        == ["language0", "language1"])


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_path_matcher_projects(project0, project1):
    vfolder = VirtualFolder.objects.create(
        name="avfolder",
        filter_rules="FOO,BAR")
    vfolder.projects.add(project0)
    vfolder.projects.add(project1)
    # no languages set so no stores
    assert list(vfolder.path_matcher.existing_stores) == []
    assert (
        sorted(vfolder.path_matcher.projects.values_list("code", flat=True))
        == ["project0", "project1"])
    vfolder.all_projects = True
    vfolder.save()
    assert vfolder.path_matcher.projects is None
    assert list(vfolder.path_matcher.languages) == []
    # no languages set so no stores
    assert list(vfolder.path_matcher.existing_stores) == []
    # didnt forget project preferences
    vfolder.all_projects = False
    vfolder.save()
    assert (
        sorted(vfolder.path_matcher.projects.values_list("code", flat=True))
        == ["project0", "project1"])


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_path_matcher_all_proj_lang():
    vfolder = VirtualFolder.objects.create(
        name="avfolder",
        all_projects=True,
        all_languages=True,
        filter_rules="*")
    assert (
        list(vfolder.path_matcher.existing_stores.order_by("pk"))
        == list(Store.objects.order_by("pk")))
    vfolder.all_languages = False
    vfolder.save()
    assert (
        list(vfolder.path_matcher.existing_stores.order_by("pk"))
        == [])
    vfolder.all_languages = True
    vfolder.all_projects = False
    vfolder.save()
    assert (
        list(vfolder.path_matcher.existing_stores.order_by("pk"))
        == [])


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_path_matcher_some_proj_lang(tp0, language1):
    vfolder = VirtualFolder.objects.create(
        name="avfolder",
        filter_rules="*")
    vfolder.languages.add(tp0.language)
    vfolder.projects.add(tp0.project)
    # m2m handler?
    vfolder.save()
    assert (
        list(vfolder.path_matcher.existing_stores.order_by("pk"))
        == list(tp0.stores.order_by("pk")))
    vfolder.languages.add(language1)
    vfolder.save()
    assert (
        list(vfolder.path_matcher.existing_stores.order_by("pk"))
        == list(
            Store.objects.filter(
                translation_project__project=tp0.project,
                translation_project__language__in=[
                    tp0.language,
                    language1]).order_by("pk")))


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_path_matcher_get_rule_regex(vfolder0, tp0, vf_rules):
    rule = vf_rules
    assert (
        vfolder0.path_matcher.get_rule_regex(rule)
        == ("^%s%s"
            % (vfolder0.path_matcher.tp_path,
               PathFilter().path_regex(rule))))
    vfolder0.filter_rules = rule
    vfolder0.languages.add(tp0.language)
    vfolder0.projects.add(tp0.project)
    vfolder0.save()
    regex = vfolder0.path_matcher.get_rule_regex(rule)
    assert (
        list(vfolder0.stores.order_by("pk"))
        == list(tp0.stores.filter(pootle_path__regex=regex).order_by("pk")))


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_path_matcher_rules(vfolder0):
    vfolder0.filter_rules = "foo,bar"
    assert (
        list(vfolder0.path_matcher.rules)
        == ["foo", "bar"])

    # convert to json field? for now be ws tolerant
    vfolder0.filter_rules = "foo, bar"
    assert (
        list(vfolder0.path_matcher.rules)
        == ["foo", "bar"])
