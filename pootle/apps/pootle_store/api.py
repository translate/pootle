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
from tastypie.resources import ModelResource

from pootle.core.api import StatisticsModelResource
from pootle_misc.stats import get_raw_stats
from pootle_store.models import Store, Suggestion, Unit


class SuggestionResource(ModelResource):
    unit = fields.ForeignKey('pootle_store.api.UnitResource', 'unit')

    class Meta:
        queryset = Suggestion.objects.all()
        resource_name = 'suggestions'
        fields = [
            'target_f',
            'translator_comment_f',
            'unit',
        ]
        list_allowed_methods = ['post']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()


class UnitResource(ModelResource):
    store = fields.ForeignKey('pootle_store.api.StoreResource', 'store')
    suggestions = fields.ToManyField(SuggestionResource, 'suggestion_set')

    class Meta:
        queryset = Unit.objects.all()
        resource_name = 'units'
        fields = [
            'commented_on',
            'context',
            'developer_comment',
            'locations',
            'mtime',
            'source_f',
            'source_length',
            'source_wordcount',
            'state',
            'store',
            'submitted_on',
            'suggestions',
            'target_f',
            'target_length',
            'target_wordcount',
            'translator_comment',
        ]
        list_allowed_methods = ['post']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()


class StoreResource(StatisticsModelResource):
    translation_project = fields.ForeignKey(
        'pootle_translationproject.api.TranslationProjectResource',
        'translation_project')
    units = fields.ToManyField(UnitResource, 'unit_set')

    class Meta:
        queryset = Store.objects.all()
        resource_name = 'stores'
        fields = [
            'file',
            'name',
            'pending',
            'pootle_path',
            'state',
            'sync_time',
            'tm',
            'translation_project',
            'units',
        ]
        list_allowed_methods = ['post']
        # HTTP methods allowed for visiting /statistics/ URLs
        statistics_allowed_methods = ['get']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()

    def retrieve_statistics(self, bundle):
        """
        Given a ``Bundle``, return the statistics for it.
        """
        return get_raw_stats(bundle.obj, include_suggestions=True)
