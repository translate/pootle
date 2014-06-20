#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from tastypie.api import Api

from pootle_language.api import LanguageResource
from accounts.api import UserResource
from pootle_project.api import ProjectResource
from pootle_store.api import StoreResource, SuggestionResource, UnitResource
from pootle_translationproject.api import TranslationProjectResource


def api_factory():
    API_VERSION = 'v1'
    pootle_api = Api(api_name=API_VERSION)
    pootle_api.register(LanguageResource())
    pootle_api.register(ProjectResource())
    pootle_api.register(StoreResource())
    pootle_api.register(SuggestionResource())
    pootle_api.register(TranslationProjectResource())
    pootle_api.register(UnitResource())
    pootle_api.register(UserResource())
    return pootle_api
