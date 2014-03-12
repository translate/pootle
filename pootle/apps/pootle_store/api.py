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
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpNotImplemented
from tastypie.resources import ModelResource

from pootle.core.api import StatisticsModelResource
from pootle_store.models import Store, Suggestion, Unit
from pootle_store.util import OBSOLETE, UNTRANSLATED, FUZZY, TRANSLATED


# Lookups that can be used on CharField fields for filtering objects.
TEXT_LOOKUPS = (
    'exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith',
    'endswith', 'iendswith',
)

# Lookups that can be used on DateTimeField fields for filtering objects.
DATE_LOOKUPS = (
    'year', 'month', 'day',
)


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
        filtering = {
            "commented_on": DATE_LOOKUPS,
            "context": TEXT_LOOKUPS,
            "developer_comment": TEXT_LOOKUPS,
            "locations": TEXT_LOOKUPS,
            "mtime": DATE_LOOKUPS,
            "source_f": TEXT_LOOKUPS,
            "state": ('exact',),
            "store": ('exact',),
            "submitted_on": DATE_LOOKUPS,
            "target_f": TEXT_LOOKUPS,
            "translator_comment": TEXT_LOOKUPS,
        }
        list_allowed_methods = ['get', 'post']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()

    def build_filters(self, filters=None):
        """Given a filters dictionary, create the necessary ORM-level filters.

        Keys should be resource fields, **NOT** model fields.

        Valid values are either a list of Django filter types (i.e.
        ``['startswith', 'exact', 'lte']``), the ``ALL`` constant or the
        ``ALL_WITH_RELATIONS`` constant.
        """
        # Convert the human-readable state names to the real values used in
        # Pootle.
        state = {
            u'untranslated': unicode(UNTRANSLATED),
            u'fuzzy': unicode(FUZZY),
            u'translated': unicode(TRANSLATED),
            u'obsolete': unicode(OBSOLETE),
        }.get(filters.get(u'state', None), None)

        if state is not None:
            filters = filters.copy()
            filters.__setitem__(u'state', state)

        return super(UnitResource, self).build_filters(filters)

    def apply_filters(self, request, applicable_filters):
        """An ORM-specific implementation of ``apply_filters``.

        The default simply applies the ``applicable_filters`` as ``**kwargs``,
        but should make it possible to do more advanced things.
        """
        # List units only when a filter criterion was provided.
        if not applicable_filters:
            raise ImmediateHttpResponse(response=HttpNotImplemented())
        return super(UnitResource, self).apply_filters(request,
                                                       applicable_filters)


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
            'pootle_path',
            'state',
            'sync_time',
            'translation_project',
            'units',
        ]
        list_allowed_methods = ['post']
        # HTTP methods allowed for visiting /statistics/ URLs
        statistics_allowed_methods = ['get']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()

    def retrieve_statistics(self, bundle):
        """Given a ``Bundle``, return the statistics for it."""
        return bundle.obj.get_stats()
