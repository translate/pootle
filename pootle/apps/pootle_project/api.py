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

from pootle_project.models import Project
from pootle_translationproject.api import TranslationProjectResource


class ProjectResource(ModelResource):
    source_language = fields.ForeignKey('pootle_language.api.LanguageResource',
                                        'source_language')
    translation_projects = fields.ToManyField(TranslationProjectResource,
                                              'translationproject_set')

    class Meta:
        queryset = Project.objects.all()
        resource_name = 'projects'
        fields = [
            'checkstyle',
            'code',
            'description',
            'fullname',
            'ignoredfiles',
            'localfiletype',
            'source_language',
            'translation_projects',
            'treestyle',
        ]
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete', 'patch']
        authorization = DjangoAuthorization()
        authentication = BasicAuthentication()
