#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from __future__ import absolute_import

from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.core.urlresolvers import reverse_lazy
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, TemplateView, UpdateView

from pootle.core.views import SuperuserRequiredMixin

from .forms import LegalPageForm
from .models import LegalPage


class AdminTemplateView(SuperuserRequiredMixin, TemplateView):

    template_name = 'staticpages/admin/list.html'

    def get_context_data(self, **kwargs):
        ctx = super(AdminTemplateView, self).get_context_data(**kwargs)
        ctx.update({
            'legalpages': LegalPage.objects.all(),
        })
        return ctx


class LegalPageCreateView(SuperuserRequiredMixin, CreateView):

    form_class = LegalPageForm
    model = LegalPage
    success_url = reverse_lazy('staticpages.admin')
    template_name = 'staticpages/admin/legalpage_create.html'


class LegalPageUpdateView(SuperuserRequiredMixin, UpdateView):

    form_class = LegalPageForm
    model = LegalPage
    success_url = reverse_lazy('staticpages.admin')
    template_name = 'staticpages/admin/legalpage_update.html'

    def get_context_data(self, **kwargs):
        ctx = super(LegalPageUpdateView, self).get_context_data(**kwargs)
        ctx.update({
            'show_delete': True,
        })
        return ctx


def legalpage(request, virtual_path):
    """The actual Legal Page."""
    lp = get_object_or_404(LegalPage, active=True,
                           virtual_path=virtual_path)

    if lp.url:
        return redirect(lp.url)

    template_name = 'staticpages/legalpage.html'
    if 'HTTP_X_FANCYBOX' in request.META:
        template_name = 'staticpages/legalpage_body.html'

    return render_to_response(template_name, {'lp': lp},
            RequestContext(request))
