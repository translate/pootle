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

try:
    from django.conf.urls import url
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import url

from tastypie.resources import ModelResource
from tastypie.utils import trailing_slash


class StatisticsModelResource(ModelResource):
    """
    A ModelResource that provides support for /resource/pk/statistics/ URLs.

    In order to use this class you must redefine the method
    ``StatisticsModelResource.retrieve_statistics`` and provide the attribute
    ``statistics_allowed_methods`` on its Meta class.
    """
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<%s>\w[\w/-]*)/statistics%s$" %
                (self._meta.resource_name, self._meta.detail_uri_name,
                trailing_slash()), self.wrap_view('dispatch_statistics'),
                name="api_dispatch_statistics"),
        ]

    def dispatch_statistics(self, request, **kwargs):
        """
        A view for handling the various HTTP methods (GET/POST/PUT/DELETE) on
        a single resource statistics.

        Relies on ``Resource.dispatch`` for the heavy-lifting.
        """
        return self.dispatch('statistics', request, **kwargs)

    def get_statistics(self, request, **kwargs):
        """
        Calls ``Resource.get_detail``

        This gets called in ``Resource.dispatch``
        """
        return self.get_detail(request, **kwargs)

    def retrieve_statistics(self, bundle):
        """
        This needs to be implemented in the subclass.

        Given a ``Bundle``, return the statistics for it.
        """
        raise NotImplementedError()

    def dehydrate(self, bundle):
        """
        A hook to allow a final manipulation of data once all fields/methods
        have built out the dehydrated data.

        Useful if you need to access more than one dehydrated field or want to
        annotate on additional data.

        Must return the modified bundle.
        """
        if bundle.request.path.endswith("/statistics/"):
            bundle.data['statistics'] = self.retrieve_statistics(bundle)
        return bundle
