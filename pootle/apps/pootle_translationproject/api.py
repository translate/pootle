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

from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization

from pootle.core.api import StatisticsModelResource
from pootle_store.api import StoreResource
from pootle_translationproject.models import TranslationProject


class TranslationProjectResource(StatisticsModelResource):
    language = fields.ForeignKey('pootle_language.api.LanguageResource',
                                 'language')
    project = fields.ForeignKey('pootle_project.api.ProjectResource',
                                'project')
    stores = fields.ToManyField(StoreResource, 'stores')

    class Meta:
        queryset = TranslationProject.objects.all()
        resource_name = 'translation-projects'
        fields = [
            'language',
            'pootle_path',
            'project',
            'real_path',
            'stores',
        ]
        list_allowed_methods = ['post']
        # HTTP methods allowed for visiting /statistics/ URLs
        statistics_allowed_methods = ['get']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()

    def retrieve_statistics(self, bundle):
        """Retrieve the statistics for the current resource object."""
        return bundle.obj.get_stats()
