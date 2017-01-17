#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import sys

import pytest

from django.urls import resolve

from pootle_fs.apps import PootleFSConfig
from pootle_fs.finder import TranslationFileFinder
from pootle_store.models import Store


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_match_filepath():

    finder = TranslationFileFinder("/path/to/<language_code>.<ext>")
    assert finder.match("/foo/baz/lang.po") is None
    assert finder.match("/path/to/lang.xliff") is None
    assert finder.match("/path/to/lang.po")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_match_reverse():
    finder = TranslationFileFinder("/path/to/<language_code>.<ext>")
    assert finder.reverse_match("foo") == "/path/to/foo.po"

    finder = TranslationFileFinder("/path/to/<language_code>/<filename>.<ext>")
    assert finder.reverse_match("foo") == "/path/to/foo/foo.po"

    finder = TranslationFileFinder("/path/to/<language_code>/<filename>.<ext>")
    assert finder.reverse_match("foo", filename="bar") == "/path/to/foo/bar.po"


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_match_reverse_directory():
    finder = TranslationFileFinder("/path/to/<language_code>.<ext>")
    assert finder.reverse_match("foo", dir_path="bar") is None

    finder = TranslationFileFinder(
        "/path/to/<dir_path>/<language_code>.<ext>")
    assert finder.reverse_match("foo") == "/path/to/foo.po"
    assert finder.reverse_match(
        "foo", dir_path="bar") == "/path/to/bar/foo.po"
    assert finder.reverse_match(
        "foo", dir_path="some/other") == "/path/to/some/other/foo.po"


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_match_stores():
    TRANSLATION_PATH = "/path/to/<dir_path>/<language_code>/<filename>.<ext>"
    finder = TranslationFileFinder(TRANSLATION_PATH)
    stores = Store.objects.all()
    for store in stores:
        kwargs = resolve(store.pootle_path).kwargs
        kwargs["filename"] = os.path.splitext(kwargs["filename"])[0]
        del kwargs["project_code"]
        expected = TRANSLATION_PATH
        for k, v in kwargs.items():
            expected = expected.replace("<%s>" % k, v)
        # clean up if no dir_path
        expected = expected.replace("//", "/")
        expected = expected.replace(
            "<ext>", str(store.filetype.extension))
        assert finder.reverse_match(**kwargs) == expected
        matched = finder.match(expected)
        for k, v in kwargs.items():
            assert matched[1][k] == v.strip("/")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_filters():
    finder = TranslationFileFinder(
        "/path/to/<dir_path>/<language_code>.<ext>",
        path_filters=["/path/to/*"])
    # doesnt filter anything
    assert finder.match("/path/to/any.po")
    assert finder.match("/path/to/some/other.po")
    assert finder.match("/path/to/and/any/other.po")

    finder = TranslationFileFinder(
        "/path/to/<dir_path>/<language_code>.<ext>",
        path_filters=["/path/to/some/*"])
    # these dont match
    assert not finder.match("/path/to/any.po")
    assert not finder.match("/path/to/and/any/other.po")
    # but this does
    assert finder.match("/path/to/some/other.po")

    # filter_paths are `and` matches
    finder = TranslationFileFinder(
        "/path/to/<dir_path>/<language_code>.<ext>",
        path_filters=["/path/to/this/*", "/path/to/this/other/*"])
    # so this doesnt match
    assert not finder.match("/path/to/this/file.po")
    # but these do
    assert finder.match("/path/to/this/other/file.po")
    assert finder.match("/path/to/this/other/file2.po")
    assert finder.match("/path/to/this/other/in/subdir/file2.po")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_match_reverse_ext():

    finder = TranslationFileFinder("/path/to/<language_code>.<ext>")

    # ext must be in list of exts
    with pytest.raises(ValueError):
        finder.reverse_match("foo", extension="abc")

    finder = TranslationFileFinder(
        "/foo/bar/<language_code>.<ext>", extensions=["abc", "xyz"])
    assert finder.reverse_match("foo") == "/foo/bar/foo.abc"
    assert finder.reverse_match("foo", extension="abc") == "/foo/bar/foo.abc"
    assert finder.reverse_match("foo", extension="xyz") == "/foo/bar/foo.xyz"


# Parametrized: ROOT_PATHS
@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_file_root(finder_root_paths):
    dir_path = os.sep.join(['', 'some', 'path'])
    path, expected = finder_root_paths
    assert (
        TranslationFileFinder(
            os.path.join(dir_path, path)).file_root
        == (
            expected
            and os.path.join(dir_path, expected)
            or dir_path))


# Parametrized: BAD_FINDER_PATHS
@pytest.mark.django_db
def test_finder_bad_paths(bad_finder_paths):
    dir_path = os.sep.join(['', 'some', 'path'])
    with pytest.raises(ValueError):
        TranslationFileFinder(os.path.join(dir_path, bad_finder_paths))


# Parametrized: FINDER_REGEXES
@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_regex(finder_regexes):
    dir_path = os.sep.join(['', 'some', 'path'])
    translation_mapping = os.path.join(dir_path, finder_regexes)
    finder = TranslationFileFinder(translation_mapping)
    path = translation_mapping
    for k, v in TranslationFileFinder.path_mapping:
        path = path.replace(k, v)
    path = os.path.splitext(path)
    path = "%s%s" % (path[0], finder._ext_re())
    assert finder.regex.pattern == "%s$" % path


# Parametrized: MATCHES
@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_match(finder_matches):
    dir_path = os.sep.join(['', 'some', 'path'])
    match_path, not_matching, matching = finder_matches
    finder = TranslationFileFinder(os.path.join(dir_path, match_path))

    for path in not_matching:
        assert not finder.match(
            os.path.join(dir_path, path))
    for path, expected in matching:
        match = finder.regex.match(os.path.join(dir_path, path))
        assert match
        named = match.groupdict()
        for k in ["lang", "dir_path", "filename", "ext"]:
            if k in expected:
                assert named[k].strip("/") == expected[k]
            else:
                assert k not in named
        reverse = finder.reverse_match(
            named['language_code'],
            named.get('filename', os.path.splitext(os.path.basename(path))[0]),
            named['ext'],
            dir_path=named.get('dir_path'))

        assert os.path.join(dir_path, path) == reverse


# Parametrized: FILES
@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_find(fs_finder):
    finder, expected = fs_finder
    assert sorted(expected) == sorted(f for f in finder.find())


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_exclude_langs():
    finder = TranslationFileFinder(
        "/path/to/<dir_path>/<language_code>.<ext>",
        exclude_languages=["foo", "bar"])
    assert not finder.match("/path/to/foo.po")
    assert not finder.match("/path/to/bar.po")
    match = finder.match("/path/to/baz.po")
    assert match[0] == "/path/to/baz.po"
    assert match[1]["language_code"] == "baz"

    assert not finder.reverse_match(language_code="foo")
    assert not finder.reverse_match(language_code="bar")
    assert (
        finder.reverse_match(language_code="baz")
        == "/path/to/baz.po")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_cache_key():
    finder = TranslationFileFinder(
        "/path/to/<dir_path>/<language_code>.<ext>",
        exclude_languages=["foo", "bar"])
    assert not finder.fs_hash
    assert not finder.cache_key
    assert finder.ns == "pootle.fs.finder"
    assert finder.sw_version == PootleFSConfig.version
    finder = TranslationFileFinder(
        "/path/to/<dir_path>/<language_code>.<ext>",
        exclude_languages=["foo", "bar"],
        fs_hash="XYZ")
    assert finder.fs_hash == "XYZ"
    assert (
        finder.cache_key
        == ("%s.%s.%s"
            % (finder.fs_hash,
               "::".join(finder.exclude_languages),
               hash(finder.regex.pattern))))


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_finder_lang_codes():
    finder = TranslationFileFinder(
        "/path/to/<dir_path>/<language_code>.<ext>")
    match = finder.match("/path/to/foo/bar@baz.po")
    assert match[1]["language_code"] == "bar@baz"
