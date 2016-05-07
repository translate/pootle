# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import fnmatch
import os
import re

import scandir

from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache


PATH_MAPPING = (
    (".", "\."),
    ("<language_code>", "(?P<language_code>[\w\-\.]*)"),
    ("<filename>", "(?P<filename>[\w\-\.]*)"),
    ("/<dir_path>/", "/<dir_path>"),
    ("<dir_path>", "(?P<dir_path>[\w\/\-]*?)"))

DEFAULT_EXTENSIONS = ("po", "pot")


class TranslationFileFinder(object):

    extensions = DEFAULT_EXTENSIONS
    path_mapping = PATH_MAPPING

    def __init__(self, translation_path, path_filters=None, extensions=None):
        TranslationPathValidator(translation_path).validate()
        self.translation_path = translation_path
        if extensions:
            self.extensions = extensions
        self.path_filters = path_filters

    @cached_property
    def regex(self):
        return re.compile(self._parse_path())

    @cached_property
    def file_root(self):
        """The deepest directory that can be used from the translation path
        before the <tags>.
        """
        file_root = self.translation_path.split("<")[0]
        if not file_root.endswith("/"):
            file_root = "/".join(file_root.split("/")[:-1])
        return file_root.rstrip("/")

    def match(self, file_path):
        """For a given file_path find translation_path matches.
        If a match is found `file_path`, `matchdata` is returned.
        """
        match = self.regex.match(file_path)
        if not match:
            return
        matched = match.groupdict()
        matched["dir_path"] = (
            matched.get("dir_path", "").strip("/"))
        if not matched.get("filename"):
            matched["filename"] = os.path.splitext(
                os.path.basename(file_path))[0]
        return file_path, matched

    def walk(self):
        """Walk a filesystem"""
        for root, dirs, files in scandir.walk(self.file_root):
            for filename in files:
                yield os.path.join(root, filename)

    def find(self):
        """Find matching files anywhere in file_root"""
        for filepath in self.walk():
            match = self.match(filepath)
            if match:
                yield match

    @lru_cache(maxsize=None)
    def reverse_match(self, language_code, filename=None,
                      extension=None, dir_path=None):
        """For given matchdata return the file path that would be
        matched.
        """
        if extension is None:
            extension = self.extensions[0]
        if extension not in self.extensions:
            raise ValueError("ext must be in the list of possible extensions")
        if not filename:
            filename = language_code
        extension = extension.strip(".")
        path = (
            "%s.%s"
            % (os.path.splitext(self.translation_path)[0], extension))
        if dir_path and "<dir_path>" not in path:
            return
        path = (path.replace("<language_code>", language_code)
                    .replace("<filename>", filename))
        if "<dir_path>" in path:
            if dir_path and dir_path.strip("/"):
                path = path.replace(
                    "<dir_path>", "/%s/" % dir_path.strip("/"))
            else:
                path = path.replace("<dir_path>", "")
        local_path = path.replace(self.file_root, "")
        if "//" in local_path:
            path = os.path.join(
                self.file_root,
                local_path.replace("//", "/").lstrip("/"))
        return path

    def _ext_re(self):
        return (
            r".(?P<ext>(%s))"
            % "|".join(
                ("%s$" % x)
                for x in set(self.extensions)))

    def _parse_path_regex(self):
        path = self.translation_path
        for k, v in self.path_mapping:
            path = path.replace(k, v)
        return r"%s%s$" % (
            os.path.splitext(path)[0],
            self._ext_re())

    def _parse_path(self):
        regex = self._parse_path_regex()
        if not self.path_filters:
            return regex
        regex = r"(?=%s)" % regex
        filter_regex = "".join(
            ("(?=^%s)" % fnmatch.translate(path))
            for path in self.path_filters)
        return r"%s%s" % (regex, filter_regex)


class TranslationPathValidator(object):

    validators = (
        "absolute", "lang_code", "ext", "match_tags", "path")

    def __init__(self, path):
        self.path = path

    def validate_absolute(self):
        if self.path != os.path.abspath(self.path):
            raise ValueError(
                "Translation path should be absolute")

    def validate_lang_code(self):
        if "<language_code>" not in self.path:
            raise ValueError(
                "Translation path must contain a <language_code> pattern to match.")

    def validate_ext(self):
        if not self.path.endswith(".<ext>"):
            raise ValueError(
                "Translation path must end with <ext>.")

    @cached_property
    def stripped_path(self):
        return (self.path.replace("<language_code>", "")
                         .replace("<dir_path>", "")
                         .replace("<ext>", "")
                         .replace("<filename>", ""))

    def validate_match_tags(self):
        if "<" in self.stripped_path or ">" in self.stripped_path:
            raise ValueError(
                "Only <language_code>, <dir_path>, <filename> and <ext> are valid "
                "patterns to match in the translation path")

    def validate_path(self):
        bad_chars = re.search("[^\w\/\-\.]+", self.stripped_path)
        if bad_chars:
            raise ValueError(
                "Invalid character in translation_path '%s'"
                % self.stripped_path[bad_chars.span()[0]:bad_chars.span()[1]])

    def validate(self):
        for k in self.validators:
            getattr(self, "validate_%s" % k)()
