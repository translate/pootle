# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
from collections import OrderedDict

from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle_config.utils import SiteConfig
from pootle_language.models import Language


logger = logging.getLogger(__name__)


class ProjectLanguageMapper(object):
    """For a given code find the relevant Pootle lang taking account of any
    lang mapping configuration.

    Presets can be defined with a dictionary of named mappings on the site_config
    `pootle.core.lang_mapping_presets`.

    Presets are enabled with a list on the project_config
    `pootle.core.use_lang_mapping_presets`.

    Lang mappings can also be configured per-project using the config setting
    `pootle.core.lang_mapping`, which should be a k, v dictionary of
    upstream_code, pootle_code. This will override any mappings in configured
    presets.
    """

    def __init__(self, project):
        self.project = project

    def __getitem__(self, k):
        return self.get_lang(k)

    def __contains__(self, k):
        return self.get_lang(k) and True or False

    @cached_property
    def site_config(self):
        return SiteConfig()

    @property
    def site_presets(self):
        """Get the pret mappings from the site config"""
        return OrderedDict(
            self.site_config.get(
                "pootle.core.lang_mapping_presets", {}))

    @property
    def project_presets(self):
        """Get the projects mapping from the Project.config"""
        return self.project.config.get(
            "pootle.core.use_lang_mapping_presets", [])

    @property
    def project_mappings(self):
        """Get the projects mapping from the Project.config"""
        return OrderedDict(
            self.project.config.get(
                "pootle.core.lang_mapping", {}))

    @property
    def mappings_from_presets(self):
        mappings = OrderedDict()
        for preset_name in self.project_presets:
            if preset_name not in self.site_presets:
                logger.warning(
                    "Unrecognised lang mapping preset: %s",
                    preset_name)
                continue
            mappings.update(self.site_presets[preset_name])
        return mappings

    @cached_property
    def lang_mappings(self):
        """Language mappings after Project.config and presets are parsed"""
        return self._parse_mappings()

    @cached_property
    def all_languages(self):
        return {
            lang.code: lang
            for lang in Language.objects.all()}

    @lru_cache()
    def get_lang(self, upstream_code):
        """Return a `Language` for a given code after mapping"""
        try:
            return self.all_languages[self.get_pootle_code(upstream_code)]
        except KeyError:
            return None

    def get_pootle_code(self, upstream_code):
        """Returns a pootle code for a given upstream code"""
        if upstream_code in self.lang_mappings:
            return self.lang_mappings[upstream_code]
        if upstream_code not in self.lang_mappings.values():
            return upstream_code

    def get_upstream_code(self, pootle_code):
        """Returns an upstream code for a given pootle code"""
        for _upstream_code, _pootle_code in self.lang_mappings.items():
            if pootle_code == _pootle_code:
                return _upstream_code
        if pootle_code not in self.lang_mappings:
            return pootle_code

    def _add_lang_to_mapping(self, upstream_code, pootle_code):
        # as its a 1 to 1 mapping remove any previous items with
        # same value
        if pootle_code in self._mapping.values():
            for k, v in self._mapping.items():
                if v == pootle_code:
                    del self._mapping[k]
                    break
        self._mapping[upstream_code] = pootle_code

    def _parse_mappings(self):
        self._mapping = OrderedDict()
        mappings = self.mappings_from_presets
        mappings.update(self.project_mappings)

        for upstream_code, pootle_code in mappings.items():
            self._add_lang_to_mapping(upstream_code, pootle_code)
        return self._mapping
