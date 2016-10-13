# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.views.generic import FormView, TemplateView

from pootle.core.views.mixins import LanguageAdminMixin, SuperuserRequiredMixin


class PootleAdminView(SuperuserRequiredMixin, TemplateView):
    pass


class PootleAdminFormView(SuperuserRequiredMixin, FormView):
    pass


class PootleLanguageAdminView(LanguageAdminMixin, TemplateView):
    pass


class PootleLanguageAdminFormView(LanguageAdminMixin, FormView):
    pass
