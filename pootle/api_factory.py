#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from tastypie.api import Api

from pootle_language.api import LanguageResource
from pootle_project.api import ProjectResource
from pootle_translationproject.api import TranslationProjectResource


def api_factory():
    API_VERSION = 'v1'
    pootle_api = Api(api_name=API_VERSION)
    pootle_api.register(LanguageResource())
    pootle_api.register(ProjectResource())
    pootle_api.register(TranslationProjectResource())
    return pootle_api
