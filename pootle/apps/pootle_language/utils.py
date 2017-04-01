# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from django.utils import translation

from pootle.core.decorators import persistent_property
from pootle_app.models import Directory

from .apps import PootleLanguageConfig
from .models import Language


class SiteLanguages(object):

    ns = "pootle.languages"
    sw_version = PootleLanguageConfig.version

    @property
    def object(self):
        return Directory.objects.select_related("revision")

    @property
    def cache_key(self):
        return (
            "all_languages",
            translation.get_language(),
            self.object.data_tool.cache_key)

    @property
    def site_languages(self):
        return Language.objects.filter(
            translationproject__isnull=False,
            translationproject__directory__obsolete=False).distinct()

    @persistent_property
    def all_languages(self):
        return {
            code: name
            for code, name
            in self.site_languages.values_list("code", "fullname")}

    @persistent_property
    def languages(self):
        langs = self.site_languages.filter(
            translationproject__project__disabled=False).distinct()
        return {
            code: name
            for code, name
            in langs.values_list("code", "fullname")}
