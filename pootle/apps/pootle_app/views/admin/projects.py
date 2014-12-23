#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014-2015 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with Pootle; if not, see <http://www.gnu.org/licenses/>.

__all__ = ('ProjectAdminView', 'ProjectAPIView')

from django.views.generic import TemplateView

from pootle.core.views import APIView, SuperuserRequiredMixin
from pootle_app.forms import ProjectForm
from pootle_misc.util import jsonify
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.filetypes import filetype_choices


class ProjectAdminView(SuperuserRequiredMixin, TemplateView):
    template_name = 'admin/projects.html'

    def get_context_data(self, **kwargs):
        languages = Language.objects.exclude(code='templates')
        language_choices = [(lang.id, unicode(lang)) for lang in languages]
        try:
            english = Language.objects.get(code='en')
            default_language = english.id
        except Language.DoesNotExist:
            default_language = languages[0].id

        kwargs['form_choices'] = jsonify({
            'checkstyle': Project.checker_choices,
            'localfiletype': filetype_choices,
            'source_language': language_choices,
            'treestyle': Project.treestyle_choices,
            'defaults': {
                'source_language': default_language,
            },
        })
        return kwargs


class ProjectAPIView(SuperuserRequiredMixin, APIView):
    model = Project
    base_queryset = Project.objects.order_by('-id')
    add_form_class = ProjectForm
    edit_form_class = ProjectForm
    page_size = 10
    search_fields = ('code', 'fullname', 'disabled')
