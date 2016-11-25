# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
from fnmatch import fnmatch

from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle.core.delegate import lang_mapper
from pootle.core.url_helpers import split_pootle_path


logger = logging.getLogger(__name__)


class FSPathMatcher(object):

    def __init__(self, context):
        self.context = context

    @cached_property
    def lang_mapper(self):
        return lang_mapper.get(
            self.project.__class__,
            instance=self.project)

    @cached_property
    def excluded_languages(self):
        excluded = self.project.config.get(
            "pootle.fs.excluded_languages")
        return [
            self.lang_mapper.get_upstream_code(code) or code
            for code
            in excluded or []]

    @lru_cache(maxsize=None)
    def get_finder(self, fs_path=None):
        path_filters = []
        if fs_path:
            path_filters.append(fs_path)
        return self.context.finder_class(
            self.translation_mapping,
            extensions=self.project.filetype_tool.valid_extensions,
            path_filters=path_filters,
            exclude_languages=self.excluded_languages,
            fs_hash=self.context.latest_hash)

    @property
    def project(self):
        return self.context.project

    @property
    def root_directory(self):
        return self.context.project.local_fs_path

    @property
    def translation_mapping(self):
        return os.path.join(
            self.project.local_fs_path,
            os.path.join(
                *self.context.project.config[
                    "pootle_fs.translation_mappings"]["default"].split("/")))

    def make_pootle_path(self, **matched):
        language_code = matched.get("language_code")
        filename = matched.get("filename")
        ext = matched.get("ext")
        if not (language_code and filename and ext):
            return
        return "/".join(
            ["", language_code,
             self.project.code]
            + [m for m in
               matched.get('dir_path', '').split("/")
               if m]
            + ["%s.%s"
               % (filename, ext)])

    def match_pootle_path(self, pootle_path_match=None, **matched):
        pootle_path = self.make_pootle_path(**matched)
        matches = (
            pootle_path
            and (not pootle_path_match
                 or fnmatch(pootle_path, pootle_path_match)))
        if matches:
            return pootle_path

    def get_language(self, language_code):
        return self.lang_mapper[language_code]

    def relative_path(self, path):
        if not path.startswith(self.root_directory):
            return path
        return path[len(self.root_directory):]

    def matches(self, fs_path, pootle_path):
        missing_langs = []
        for file_path, matched in self.get_finder(fs_path).found:
            if matched["language_code"] in missing_langs:
                continue
            language = self.get_language(matched["language_code"])
            if not language:
                missing_langs.append(matched['language_code'])
                continue
            matched["language_code"] = language.code
            matched_pootle_path = self.match_pootle_path(
                pootle_path_match=pootle_path, **matched)
            if matched_pootle_path:
                yield matched_pootle_path, self.relative_path(file_path)
        if missing_langs:
            logger.warning(
                "Could not import files for languages: %s",
                (", ".join(sorted(missing_langs))))

    def reverse_match(self, pootle_path):
        lang_code, __, dir_path, filename = split_pootle_path(pootle_path)
        lang_code = self.lang_mapper.get_upstream_code(lang_code)
        fileparts = os.path.splitext(filename)
        fs_path = self.get_finder().reverse_match(
            lang_code,
            filename=fileparts[0],
            extension=fileparts[1].lstrip("."),
            dir_path=dir_path.strip("/"))
        if fs_path:
            return "/%s" % self.relative_path(fs_path).lstrip("/")
