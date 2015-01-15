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

from django.contrib.sites.models import Site

from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization

from pootle.core.api import StatisticsModelResource
from pootle_project.models import Project
from pootle_translationproject.api import TranslationProjectResource


class ProjectResource(StatisticsModelResource):
    source_language = fields.ForeignKey(
        'pootle_language.api.LanguageResource',
        'source_language',
    )
    translation_projects = fields.ToManyField(
        TranslationProjectResource,
        'translationproject_set',
    )

    class Meta:
        queryset = Project.objects.all()
        resource_name = 'projects'
        fields = [
            'checkstyle',
            'code',
            'fullname',
            'ignoredfiles',
            'localfiletype',
            'source_language',
            'translation_projects',
            'treestyle',
        ]
        always_return_data = True
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete', 'patch']
        # HTTP methods allowed for visiting /statistics/ URLs.
        statistics_allowed_methods = ['get']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()

    def dehydrate(self, bundle):
        # Include a custom 'backlink' field.
        bundle.data['backlink'] = ('http://%s%s' %
                                   (Site.objects.get_current().domain,
                                    bundle.obj.get_absolute_url()))
        return bundle

    def retrieve_statistics(self, bundle):
        """Retrieve the statistics for the current resource object."""
        return bundle.obj.get_stats()
