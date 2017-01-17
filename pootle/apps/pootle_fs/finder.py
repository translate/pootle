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

from pootle.core.decorators import persistent_property

from .apps import PootleFSConfig


PATH_MAPPING = (
    (".", "\."),
    ("<language_code>", "(?P<language_code>[\w\@\-\.]*)"),
    ("<filename>", "(?P<filename>[\w\-\.]*)"),
    ("/<dir_path>/", "/<dir_path>"),
    ("<dir_path>", "(?P<dir_path>[\w\/\-]*?)"))

DEFAULT_EXTENSIONS = ("po", "pot")


class TranslationFileFinder(object):
    ns = "pootle.fs.finder"
    sw_version = PootleFSConfig.version
    extensions = DEFAULT_EXTENSIONS
    path_mapping = PATH_MAPPING

    def __init__(self, translation_mapping, path_filters=None,
                 extensions=None, exclude_languages=None, fs_hash=None):
        self.fs_hash = fs_hash
        TranslationMappingFinderValidator(translation_mapping).validate()
        self.translation_mapping = translation_mapping
        if extensions:
            self.extensions = extensions
        self.path_filters = path_filters
        self.exclude_languages = exclude_languages or []

    @cached_property
    def regex(self):
        return re.compile(self._parse_path())

    @cached_property
    def file_root(self):
        """The deepest directory that can be used from the translation mapping
        before the <tags>.
        """
        file_root = self.translation_mapping.split("<")[0]
        if not file_root.endswith("/"):
            file_root = os.sep.join(file_root.split("/")[:-1])
        return file_root.rstrip("/")

    def match(self, file_path):
        """For a given file_path find translation_mapping matches.
        If a match is found `file_path`, `matchdata` is returned.
        """
        match = self.regex.match(file_path)
        if not match:
            return
        matched = match.groupdict()
        if matched["language_code"] in self.exclude_languages:
            return
        matched["dir_path"] = matched.get("dir_path", "").strip("/")
        if not matched.get("filename"):
            matched["filename"] = os.path.splitext(
                os.path.basename(file_path))[0]
        return file_path, matched

    def walk(self):
        """Walk a filesystem"""
        for root, dirs_, files in scandir.walk(self.file_root):
            for filename in files:
                yield os.path.join(root, filename)

    def find(self):
        """Find matching files anywhere in file_root"""
        for filepath in self.walk():
            match = self.match(filepath)
            if match:
                yield match

    @property
    def cache_key(self):
        if not self.fs_hash:
            return
        return (
            "%s.%s.%s"
            % (self.fs_hash,
               "::".join(self.exclude_languages),
               hash(self.regex.pattern)))

    @persistent_property
    def found(self):
        return list(self.find())

    @lru_cache(maxsize=None)
    def reverse_match(self, language_code, filename=None,
                      extension=None, dir_path=None):
        """For given matchdata return the file path that would be
        matched.
        """
        if language_code in self.exclude_languages:
            return
        if extension is None:
            extension = self.extensions[0]
        if extension not in self.extensions:
            raise ValueError("ext must be in the list of possible extensions")
        if not filename:
            filename = language_code
        extension = extension.strip(".")
        path = (
            "%s.%s"
            % (os.path.splitext(self.translation_mapping)[0], extension))
        if dir_path and "<dir_path>" not in path:
            return
        path = (path.replace("<language_code>", language_code)
                    .replace("<filename>", filename))
        if "<dir_path>" in path:
            if dir_path and dir_path.strip("/"):
                path = path.replace("<dir_path>", "/%s/" % dir_path.strip("/"))
            else:
                path = path.replace("<dir_path>", "")
        local_path = path.replace(self.file_root, "")
        if "//" in local_path:
            path = "/".join([
                self.file_root,
                local_path.replace("//", "/").lstrip("/")])
        return path

    def _ext_re(self):
        return (
            r".(?P<ext>(%s))"
            % "|".join(
                ("%s$" % x)
                for x in set(self.extensions)))

    def _parse_path_regex(self):
        path = self.translation_mapping
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


class TranslationMappingValidator(object):

    validators = (
        "absolute", "lang_code", "ext", "match_tags", "path")

    def __init__(self, path):
        self.path = path

    def validate_absolute(self):
        if self.path[0] != '/':
            raise ValueError(
                "Translation mapping '%s' should start with '/'" % self.path)

    def validate_lang_code(self):
        if "<language_code>" not in self.path:
            raise ValueError(
                "Translation mapping must contain a <language_code> pattern "
                "to match.")

    def validate_ext(self):
        if not self.path.endswith(".<ext>"):
            raise ValueError(
                "Translation mapping must end with <ext>.")

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
                "patterns to match in the translation mapping")

    def validate_path(self):
        if os.path.sep == "\\":
            bad_chars = re.search("[^\w\\\:\-\.]+", self.stripped_path)
        else:
            bad_chars = re.search("[^\w\/\-\.]+", self.stripped_path)
        if bad_chars:
            raise ValueError(
                "Invalid character in translation_mapping '%s'"
                % self.stripped_path[bad_chars.span()[0]:bad_chars.span()[1]])

    def validate(self):
        for k in self.validators:
            getattr(self, "validate_%s" % k)()


class TranslationMappingFinderValidator(TranslationMappingValidator):

    def validate_absolute(self):
        if self.path != os.path.abspath(self.path):
            raise ValueError(
                "Translation mapping '%s' should be absolute" % self.path)
