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

from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization

from pootle.core.api import StatisticsModelResource
from pootle_language.models import Language
from pootle_misc.stats import get_raw_stats
from pootle_translationproject.api import TranslationProjectResource


class LanguageResource(StatisticsModelResource):
    translation_projects = fields.ToManyField(TranslationProjectResource,
                                              'translationproject_set')

    class Meta:
        queryset = Language.objects.all()
        resource_name = 'languages'
        fields = [
            'code',
            'description',
            'fullname',
            'nplurals',
            'pluralequation',
            'specialchars',
            'translation_projects',
        ]
        # HTTP methods allowed for visiting /statistics/ URLs
        statistics_allowed_methods = ['get']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()

    def retrieve_statistics(self, bundle):
        """
        Given a ``Bundle``, return the statistics for it.
        """
        return get_raw_stats(bundle.obj, include_suggestions=True)
