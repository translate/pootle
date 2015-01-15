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
from pootle_translationproject.api import TranslationProjectResource


# Lookups that can be used on CharField fields for filtering objects.
TEXT_LOOKUPS = (
    'exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith',
    'endswith', 'iendswith',
)


class LanguageResource(StatisticsModelResource):
    translation_projects = fields.ToManyField(TranslationProjectResource,
                                              'translationproject_set')

    class Meta:
        queryset = Language.objects.all()
        resource_name = 'languages'
        fields = [
            'code',
            'fullname',
            'nplurals',
            'pluralequation',
            'specialchars',
            'translation_projects',
        ]
        filtering = {
            "code": TEXT_LOOKUPS,
        }
        # HTTP methods allowed for visiting /statistics/ URLs.
        statistics_allowed_methods = ['get']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()

    def retrieve_statistics(self, bundle):
        """Retrieve the statistics for the current resource object."""
        return bundle.obj.get_stats()
