# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.views.generic import TemplateView

from pootle.core.views import APIView
from pootle.core.views.mixins import SuperuserRequiredMixin
from pootle_app.forms import LanguageForm
from pootle_language.models import Language


__all__ = ('LanguageAdminView', 'LanguageAPIView')


class LanguageAdminView(SuperuserRequiredMixin, TemplateView):
    template_name = 'admin/languages.html'

    def get_context_data(self, **kwargs):
        return {
            'page': 'admin-languages',
        }


class LanguageAPIView(SuperuserRequiredMixin, APIView):
    model = Language
    base_queryset = Language.objects.order_by('-id')
    add_form_class = LanguageForm
    edit_form_class = LanguageForm
    page_size = 10
    search_fields = ('code', 'fullname')
