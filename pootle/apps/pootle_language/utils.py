# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.lang.data import get_language_iso_fullname

from django.conf import settings
from django.utils.translation import get_language

from pootle.core import language
from pootle.core.decorators import persistent_property
from pootle.core.delegate import language_code, revision
from pootle.i18n.gettext import tr_lang
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
    def request_lang(self):
        return get_language()

    @property
    def cache_key(self):
        rev_context = self.object
        return (
            "all_languages",
            self.request_lang,
            revision.get(rev_context.__class__)(
                rev_context).get(key="languages"))

    @property
    def site_languages(self):
        langs = Language.objects.filter(
            translationproject__isnull=False,
            translationproject__directory__obsolete=False).distinct()
        return langs.values_list("code", "fullname")

    def capitalize(self, language_name):
        if self.request_lang in language.UPPERCASE_UI:
            return "".join(
                [language_name[0].upper(), language_name[1:]])
        return language_name

    def localised_languages(self, langs):
        matches = False
        if self.request_lang:
            server_code = language_code.get()(settings.LANGUAGE_CODE)
            request_code = language_code.get()(self.request_lang)
            matches = server_code.matches(request_code)
        if matches:
            trans_func = lambda code, name: name
        else:
            trans_func = lambda code, name: self.capitalize(
                tr_lang(
                    get_language_iso_fullname(code)
                    or name))
        return {
            code: trans_func(code, name)
            for code, name
            in langs}

    @persistent_property
    def all_languages(self):
        return self.localised_languages(self.site_languages)

    @persistent_property
    def languages(self):
        return self.localised_languages(
            self.site_languages.filter(
                translationproject__project__disabled=False).distinct())
