# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from collections import OrderedDict

import pytest


BAD_FINDER_PATHS = [
    "lang/foo.<ext>",
    "<language_code>/<foo>.<ext>",
    "<language_code>/foo.po",
    "../<language_code>/foo.<ext>",
    "<language_code>/../foo.<ext>",
    "<language_code>/..",
    "foo/@<language_code>/bar.<ext>"]

ROOT_PATHS = OrderedDict()
ROOT_PATHS["<language_code>.<ext>"] = ""
ROOT_PATHS["foo/<language_code>.<ext>"] = "foo"
ROOT_PATHS["foo/bar/baz-<filename>-<language_code>.<ext>"] = "foo/bar"

MATCHES = OrderedDict()
MATCHES["po/<language_code>.<ext>"] = (
    ["en.po", "foo/bar/en.po"],
    [("po/en.po", dict(language_code="en", ext="po"))])
MATCHES["po-<filename>/<language_code>.<ext>"] = (
    ["en.po", "po/en.po"],
    [("po-foo/en.po", dict(language_code="en", filename="foo", ext="po"))])
MATCHES["po/<filename>-<language_code>.<ext>"] = (
    ["en.po", "po/en.po"],
    [("po/foo-en.po", dict(language_code="en", filename="foo", ext="po"))])
MATCHES["<language_code>/<dir_path>/<filename>.<ext>"] = (
    ["foo.po"],
    [("en/foo.po",
      dict(language_code="en", dir_path="", filename="foo", ext="po")),
     ("en/foo.pot",
      dict(language_code="en", dir_path="", filename="foo", ext="pot")),
     ("en/bar/baz/foo.po",
      dict(language_code="en", dir_path="bar/baz", filename="foo", ext="po"))])
MATCHES["<dir_path>/<language_code>/<filename>.<ext>"] = (
    ["foo.po", "en/foo.poo"],
    [("en/foo.po",
      dict(language_code="en", dir_path="", filename="foo", ext="po")),
     ("en/foo.pot",
      dict(language_code="en", dir_path="", filename="foo", ext="pot")),
     ("bar/baz/en/foo.po",
      dict(language_code="en", dir_path="bar/baz", filename="foo", ext="po"))])

FINDER_REGEXES = [
    "<language_code>.<ext>",
    "<language_code>/<filename>.<ext>",
    "<dir_path>/<language_code>.<ext>",
    "<language_code><dir_path>/<filename>.<ext>"]

FILES = OrderedDict()
FILES["gnu_style/po/<language_code>.<ext>"] = (
    ("gnu_style/po/language0.po",
     dict(language_code="language0",
          ext="po",
          filename="language0",
          dir_path="")),
    ("gnu_style/po/language1.po",
     dict(language_code="language1",
          ext="po",
          filename="language1",
          dir_path="")))
FILES["gnu_style_named_files/po/<filename>-<language_code>.<ext>"] = (
    ("gnu_style_named_files/po/example1-language1.po",
     dict(language_code="language1",
          filename="example1",
          ext="po",
          dir_path="")),
    ("gnu_style_named_files/po/example1-language0.po",
     dict(language_code="language0",
          filename="example1",
          ext="po",
          dir_path="")),
    ("gnu_style_named_files/po/example2-language1.po",
     dict(language_code="language1",
          filename="example2",
          ext="po",
          dir_path="")),
    ("gnu_style_named_files/po/example2-language0.po",
     dict(language_code="language0",
          filename="example2",
          ext="po",
          dir_path="")))
FILES["gnu_style_named_folders/po-<filename>/<language_code>.<ext>"] = (
    ("gnu_style_named_folders/po-example1/language1.po",
     dict(language_code="language1",
          filename="example1",
          ext="po",
          dir_path="")),
    ("gnu_style_named_folders/po-example1/language0.po",
     dict(language_code="language0",
          filename="example1",
          ext="po",
          dir_path="")),
    ("gnu_style_named_folders/po-example2/language1.po",
     dict(language_code="language1",
          filename="example2",
          ext="po",
          dir_path="")),
    ("gnu_style_named_folders/po-example2/language0.po",
     dict(language_code="language0",
          filename="example2",
          ext="po",
          dir_path="")))
FILES["non_gnu_style/locales/<language_code>/<dir_path>/<filename>.<ext>"] = (
    ("non_gnu_style/locales/language1/example1.po",
     dict(language_code=u"language1",
          filename=u"example1",
          ext=u"po",
          dir_path=u"")),
    ("non_gnu_style/locales/language0/example1.po",
     dict(language_code=u"language0",
          filename=u"example1",
          ext=u"po",
          dir_path=u"")),
    ("non_gnu_style/locales/language1/example2.po",
     dict(language_code=u"language1",
          filename=u"example2",
          ext=u"po",
          dir_path=u"")),
    ("non_gnu_style/locales/language0/example2.po",
     dict(language_code=u"language0",
          filename=u"example2",
          ext=u"po",
          dir_path=u"")),
    ("non_gnu_style/locales/language1/subsubdir/example3.po",
     dict(language_code=u"language1",
          filename=u"example3",
          ext=u"po",
          dir_path=u"subsubdir")),
    ("non_gnu_style/locales/language0/subsubdir/example3.po",
     dict(language_code=u"language0",
          filename=u"example3",
          ext=u"po",
          dir_path=u"subsubdir")),
    ("non_gnu_style/locales/language1/subsubdir/example4.po",
     dict(language_code=u"language1",
          filename=u"example4",
          ext=u"po",
          dir_path=u"subsubdir")),
    ("non_gnu_style/locales/language0/subsubdir/example4.po",
     dict(language_code=u"language0",
          filename=u"example4",
          ext=u"po",
          dir_path=u"subsubdir")))


@pytest.fixture(params=FINDER_REGEXES)
def finder_regexes(request):
    return request.param


@pytest.fixture(params=BAD_FINDER_PATHS)
def bad_finder_paths(request):
    return request.param


@pytest.fixture(params=FILES.keys())
def finder_files(request):
    return request.param, FILES[request.param]


@pytest.fixture
def fs_finder(test_fs, finder_files):
    from pootle_fs.finder import TranslationFileFinder

    translation_mapping, expected = finder_files
    test_filepath = test_fs.path("data/fs/example_fs")

    finder = TranslationFileFinder(
        os.path.join(
            test_filepath,
            translation_mapping))
    expected = [
        (os.path.join(test_filepath, path), parsed)
        for path, parsed
        in expected]
    return finder, expected


@pytest.fixture(params=MATCHES.keys())
def finder_matches(request):
    return [request.param] + list(MATCHES[request.param])


@pytest.fixture(params=ROOT_PATHS.keys())
def finder_root_paths(request):
    return request.param, ROOT_PATHS[request.param]
