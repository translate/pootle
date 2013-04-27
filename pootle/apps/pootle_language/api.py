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
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource

from pootle_language.models import Language
from pootle_translationproject.models import TranslationProject


class LanguageResource(ModelResource):
    class Meta:
        tp_qs = TranslationProject.objects.distinct()
        tp_qs = tp_qs.exclude(language__code='templates')
        langs_qs = tp_qs.values_list('language__code', flat=True)
        queryset = Language.objects.filter(code__in=langs_qs).order_by('code')
        resource_name = 'languages'
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()
