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

from django.contrib.auth.models import User

from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization

from pootle.core.api import StatisticsModelResource
from pootle_profile.models import PootleProfile


class UserResource(StatisticsModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'users'
        fields = [
            'date_joined',
            'email',
            'first_name',
            'last_name',
            'username',
        ]
        list_allowed_methods = ['post']
        # List of fields shown when visiting /statistics/
        statistics_fields = [
            'statistics',
            'username',
        ]
        # HTTP methods allowed for visiting /statistics/ URLs
        statistics_allowed_methods = ['get']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()

    def retrieve_statistics(self, bundle):
        """Retrieve the statistics for the current resource object."""
        up = PootleProfile.objects.get(user=bundle.obj)
        return up.contributions

    def dehydrate(self, bundle):
        """A hook to allow final manipulation of data.

        It is run after all fields/methods have built out the dehydrated data.

        Useful if you need to access more than one dehydrated field or want to
        annotate on additional data.

        Must return the modified bundle.
        """
        bundle = super(UserResource, self).dehydrate(bundle)
        if not bundle.obj == bundle.request.user:
            # Remove sensitive data when other users look at the statistics for
            # a given user.
            for field in self._meta.fields:
                if field not in self._meta.statistics_fields:
                    bundle.data.pop(field, None)
        return bundle
