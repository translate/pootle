# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from django.utils import translation

from pootle.core.decorators import persistent_property
from pootle.core.delegate import revision
from pootle_app.models import Directory

from .apps import PootleLanguageConfig
from .models import Language


class SiteLanguages(object):

    ns = "pootle.languages"
    sw_version = PootleLanguageConfig.version

    @property
    def object(self):
        return Directory.objects.root

    @property
    def server_lang(self):
        return translation.get_language()

    @property
    def cache_key(self):
        rev_context = self.object
        return (
            "all_languages",
            self.server_lang,
            revision.get(rev_context.__class__)(rev_context).get(key="stats"))

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
