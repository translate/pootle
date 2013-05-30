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

from pootle_store.models import Store


class StoreResource(ModelResource):
    translation_project = fields.ForeignKey(
        'pootle_translationproject.api.TranslationProjectResource',
        'translation_project')

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
        ]
        list_allowed_methods = ['post']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()
