# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import language_code, language_team, site_languages
from pootle.core.language import LanguageCode
from pootle.core.plugin import getter

from .teams import LanguageTeam
from .utils import SiteLanguages


_site_languages = SiteLanguages()


@getter(language_code)
def language_code_getter(**kwargs_):
    return LanguageCode


@getter(language_team)
def language_team_getter(**kwargs_):
    return LanguageTeam


@getter(site_languages)
def site_languages_getter(**kwargs_):
    return _site_languages
