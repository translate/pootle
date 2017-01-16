#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import random
import sys
from collections import OrderedDict

import pytest

from django.urls import resolve

from pootle_fs.finder import TranslationFileFinder
from pootle_fs.matcher import FSPathMatcher
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_project.lang_mapper import ProjectLanguageMapper
from pootle_store.models import Store


TEST_LANG_MAPPING = OrderedDict(
    [["en_FOO", "en"],
     ["language0_FOO", "language0"],
     ["language1_FOO", "language1"]])


TEST_LANG_MAPPING_BAD = OrderedDict(
    [["en_FOO", "en"],
     ["language0_FOO", "language0"],
     ["language1_FOO", "language1 XXX"]])


class DummyFinder(TranslationFileFinder):

    @property
    def dummy_paths(self):
        paths = []
        for pootle_path in self.pootle_paths:
            match = resolve(pootle_path).kwargs
            excluded_languages = self.project.config.get(
                "pootle.fs.excluded_languages", [])
            if match["language_code"] in excluded_languages:
                continue
            match["filename"], match["ext"] = os.path.splitext(
                match["filename"])
            match["ext"] = match["ext"][1:]
            dir_path = (
                "%s/" % match["dir_path"]
                if match["dir_path"]
                else "")
            fs_path = (
                "/path/to/%s/%s/%s%s.%s"
                % (self.project.code,
                   match["language_code"],
                   dir_path,
                   match["filename"],
                   match["ext"]))
            paths.append((fs_path, match))
        return paths

    def find(self):
        return self.dummy_paths


class DummyContext(object):

    def __init__(self, project):
        self.project = project

    @property
    def latest_hash(self):
        return hash(random.random())

    @property
    def finder_class(self):
        project = self.project
        pootle_paths = list(
            Store.objects.filter(translation_project__project=self.project)
                         .values_list("pootle_path", flat=True))

        class DummyFinderClosure(DummyFinder):

            def __init__(self, *args, **kwargs):
                self.project = project
                self.pootle_paths = pootle_paths
                super(DummyFinderClosure, self).__init__(*args, **kwargs)

        return DummyFinderClosure


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_matcher_instance(settings):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    translation_mapping = "<language_code>/<dir_path>/<filename>.<ext>"
    project = Project.objects.get(code="project0")
    project.config[
        "pootle_fs.translation_mappings"] = dict(default=translation_mapping)
    context = DummyContext(project)
    matcher = FSPathMatcher(context)
    assert matcher.project == project
    assert matcher.root_directory == project.local_fs_path
    assert matcher.translation_mapping == os.path.join(
        project.local_fs_path, translation_mapping.lstrip("/"))


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_matcher_finder(settings):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project = Project.objects.get(code="project0")
    project.config["pootle_fs.translation_mappings"] = dict(
        default="/<language_code>/<dir_path>/<filename>.<ext>")
    matcher = FSPathMatcher(DummyContext(project))
    finder = matcher.get_finder()
    assert isinstance(finder, DummyFinder)
    assert finder.translation_mapping == matcher.translation_mapping
    finder = matcher.get_finder(fs_path="bar")
    assert finder.translation_mapping == matcher.translation_mapping
    assert finder.path_filters == ["bar"]


@pytest.mark.django_db
def test_matcher_get_lang():
    project = Project.objects.get(code="project0")
    project.config["pootle_fs.translation_mappings"] = dict(
        default="/path/to/<language_code>/<dir_path>/<filename>.<ext>")
    project.config["pootle.core.lang_mapping"] = {
        "upstream-language0": "language0"}
    matcher = FSPathMatcher(DummyContext(project))
    assert (
        matcher.get_language("upstream-language0")
        == Language.objects.get(code="language0"))


@pytest.mark.django_db
def test_matcher_make_pootle_path(settings):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project = Project.objects.get(code="project0")
    project.config["pootle_fs.translation_mappings"] = dict(
        default="/path/to/<language_code>/<dir_path>/<filename>.<ext>")
    matcher = FSPathMatcher(DummyContext(project))
    assert matcher.make_pootle_path() is None
    # must provide language_code, filename and ext at a min
    assert matcher.make_pootle_path(language_code="foo") is None
    assert (
        matcher.make_pootle_path(language_code="foo", filename="bar")
        is None)
    assert (
        matcher.make_pootle_path(language_code="foo", ext="baz")
        is None)
    assert (
        matcher.make_pootle_path(
            language_code="foo", filename="bar", ext="baz")
        == "/foo/%s/bar.baz" % project.code)
    assert (
        matcher.make_pootle_path(
            language_code="foo", filename="bar", ext="baz", dir_path="sub/dir")
        == u'/foo/%s/sub/dir/bar.baz' % project.code)
    assert (
        matcher.make_pootle_path(
            language_code="foo", filename="bar", ext="baz", dir_path="sub/dir/")
        == u'/foo/%s/sub/dir/bar.baz' % project.code)
    assert (
        matcher.make_pootle_path(
            language_code="foo", filename="bar", ext="baz", dir_path="/sub/dir")
        == u'/foo/%s/sub/dir/bar.baz' % project.code)


@pytest.mark.django_db
def test_matcher_match_pootle_path(settings):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project = Project.objects.get(code="project0")
    project.config["pootle_fs.translation_mappings"] = dict(
        default="/path/to/<language_code>/<dir_path>/<filename>.<ext>")
    matcher = FSPathMatcher(DummyContext(project))

    assert matcher.match_pootle_path(language_code="foo") is None
    assert (
        matcher.match_pootle_path(language_code="foo", filename="bar")
        is None)
    assert (
        matcher.match_pootle_path(language_code="foo", ext="baz")
        is None)
    assert (
        matcher.match_pootle_path(
            language_code="foo", filename="bar", ext="baz")
        == "/foo/%s/bar.baz" % project.code)
    assert (
        matcher.match_pootle_path(
            language_code="foo", filename="bar", ext="baz", dir_path="sub/dir")
        == u'/foo/%s/sub/dir/bar.baz' % project.code)
    assert (
        matcher.match_pootle_path(
            language_code="foo", filename="bar", ext="baz", dir_path="sub/dir/")
        == u'/foo/%s/sub/dir/bar.baz' % project.code)
    assert (
        matcher.match_pootle_path(
            language_code="foo", filename="bar", ext="baz", dir_path="/sub/dir")
        == u'/foo/%s/sub/dir/bar.baz' % project.code)
    assert (
        matcher.match_pootle_path(
            pootle_path_match="/foo*",
            language_code="foo", filename="bar", ext="baz", dir_path="/sub/dir")
        == u'/foo/%s/sub/dir/bar.baz' % project.code)
    assert (
        matcher.match_pootle_path(
            pootle_path_match="*sub/dir/*",
            language_code="foo", filename="bar", ext="baz", dir_path="/sub/dir")
        == u'/foo/%s/sub/dir/bar.baz' % project.code)
    assert (
        matcher.match_pootle_path(
            pootle_path_match="*/bar.baz",
            language_code="foo", filename="bar", ext="baz", dir_path="/sub/dir")
        == u'/foo/%s/sub/dir/bar.baz' % project.code)
    assert (
        matcher.match_pootle_path(
            pootle_path_match="/foo",
            language_code="foo", filename="bar", ext="baz", dir_path="/sub/dir")
        is None)


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_matcher_relative_path(settings):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project = Project.objects.get(code="project0")
    project.config["pootle_fs.translation_mappings"] = dict(
        default="/path/to/<language_code>/<dir_path>/<filename>.<ext>")
    matcher = FSPathMatcher(DummyContext(project))
    assert matcher.relative_path("/foo/bar") is "/foo/bar"
    assert (
        matcher.relative_path(os.path.join(matcher.root_directory, "foo/bar"))
        == "/foo/bar")
    assert (
        matcher.relative_path(
            os.path.join(
                "/foo/bar",
                matcher.root_directory.lstrip("/"),
                "foo/bar"))
        == os.path.join(
            "/foo/bar",
            matcher.root_directory.lstrip("/"),
            "foo/bar"))
    assert (
        matcher.relative_path(
            os.path.join(
                matcher.root_directory,
                "foo/bar",
                matcher.root_directory.lstrip("/"),
                "foo/bar"))
        == os.path.join(
            "/foo/bar",
            matcher.root_directory.lstrip("/"),
            "foo/bar"))


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_matcher_matches(settings):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project = Project.objects.get(code="project0")
    project.config["pootle_fs.translation_mappings"] = dict(
        default="/some/other/path/<language_code>/<dir_path>/<filename>.<ext>")
    matcher = FSPathMatcher(DummyContext(project))
    finder = matcher.get_finder()
    matches = []
    for file_path, matched in finder.dummy_paths:
        language = matcher.get_language(matched["language_code"])
        matched["language_code"] = language.code
        matches.append(
            (matcher.match_pootle_path(**matched),
             matcher.relative_path(file_path)))
    assert matches == list(matcher.matches(None, None))


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_matcher_matches_missing_langs(settings, caplog, no_templates_tps):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project = Project.objects.get(code="project0")
    project.config["pootle_fs.translation_mappings"] = dict(
        default="/some/other/path/<language_code>/<dir_path>/<filename>.<ext>")
    project.config["pootle.core.lang_mapping"] = {
        "language0": "language0-DOES_NOT_EXIST",
        "language1": "language1-DOES_NOT_EXIST"}

    matcher = FSPathMatcher(DummyContext(project))
    assert list(matcher.matches(None, None)) == []
    assert (
        "Could not import files for languages: language0, language1"
        in caplog.text)


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_matcher_reverse_match(settings):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project = Project.objects.get(code="project0")
    project.config["pootle_fs.translation_mappings"] = dict(
        default="/<language_code>/<dir_path>/<filename>.<ext>")
    project.config["pootle.core.lang_mapping"] = {
        "upstream-foo": "foo"}
    matcher = FSPathMatcher(DummyContext(project))
    assert (
        matcher.reverse_match("/foo/%s/bar.po" % project.code)
        == "/upstream-foo/bar.po")
    assert (
        matcher.reverse_match("/foo/%s/some/path/bar.po" % project.code)
        == "/upstream-foo/some/path/bar.po")

    with pytest.raises(ValueError):
        matcher.reverse_match("/foo/%s/bar.not" % project.code)


@pytest.mark.django_db
def test_matcher_language_mapper(english, settings):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project = Project.objects.get(code="project0")
    matcher = FSPathMatcher(DummyContext(project))
    assert "pootle.core.lang_mapping" not in project.config
    assert isinstance(matcher.lang_mapper, ProjectLanguageMapper)
    assert matcher.lang_mapper.lang_mappings == {}
    assert matcher.lang_mapper["en_FOO"] is None
    assert matcher.lang_mapper.get_pootle_code("en") == "en"
    assert matcher.lang_mapper.get_pootle_code("en_FOO") == "en_FOO"
    assert matcher.lang_mapper.get_upstream_code("en") == "en"
    project.config["pootle.core.lang_mapping"] = TEST_LANG_MAPPING
    assert matcher.lang_mapper.lang_mappings == {}
    matcher = FSPathMatcher(DummyContext(project))
    assert matcher.lang_mapper.lang_mappings == TEST_LANG_MAPPING
    assert "en_FOO" in matcher.lang_mapper
    assert matcher.lang_mapper["en_FOO"] == english


@pytest.mark.django_db
def test_matcher_language_mapper_bad(settings):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project = Project.objects.get(code="project0")
    language1 = Language.objects.get(code="language1")
    project.config["pootle.core.lang_mapping"] = TEST_LANG_MAPPING_BAD
    # bad configuration lines are ignored
    matcher = FSPathMatcher(DummyContext(project))
    assert "language1_FOO" not in matcher.lang_mapper
    assert matcher.lang_mapper["language1_FOO"] is None
    assert matcher.lang_mapper["language1"] == language1


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_matcher_matches_excluded_langs(settings, caplog, project0, language0):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project0.config["pootle_fs.translation_mappings"] = dict(
        default="/some/other/path/<language_code>/<dir_path>/<filename>.<ext>")
    project0.config["pootle.fs.excluded_languages"] = [language0.code]
    matcher = FSPathMatcher(DummyContext(project0))
    assert matcher.excluded_languages == [language0.code]
    assert matcher.get_finder().exclude_languages == [language0.code]
    assert not any(
        m[0].startswith("/%s/" % language0.code)
        for m in matcher.matches(None, None))


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_matcher_matches_excluded_mapped_langs(settings, caplog,
                                               project0, language0):
    settings.POOTLE_FS_WORKING_PATH = os.sep.join(['', 'path', 'to'])
    project0.config["pootle_fs.translation_mappings"] = dict(
        default="/some/other/path/<language_code>/<dir_path>/<filename>.<ext>")
    project0.config["pootle.fs.excluded_languages"] = [language0.code]
    project0.config["pootle.core.lang_mapping"] = OrderedDict(
        [["%s_FOO" % language0.code, language0.code]])
    matcher = FSPathMatcher(DummyContext(project0))
    assert matcher.excluded_languages == ["%s_FOO" % language0.code]
    assert matcher.get_finder().exclude_languages == ["%s_FOO" % language0.code]
    assert not any(
        m[0].startswith("/%s/" % language0.code)
        for m in matcher.matches(None, None))
    assert matcher.matches(None, None)
