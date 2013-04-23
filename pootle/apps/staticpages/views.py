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

from django.shortcuts import redirect, render_to_response
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse_lazy
from django.http import Http404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, TemplateView, UpdateView

from pootle.core.views import SuperuserRequiredMixin

from .models import AbstractPage, LegalPage


class PageModelMixin(object):
    """Mixin used to set the view's page model according to the
    `page_type` argument caught in a url pattern.
    """

    def dispatch(self, request, *args, **kwargs):
        self.model = {
            'legal': LegalPage,
        }.get(kwargs.get('page_type', None))

        if self.model is None:
            raise Http404

        return super(PageModelMixin, self).dispatch(request, *args, **kwargs)


class AdminTemplateView(SuperuserRequiredMixin, TemplateView):

    template_name = 'staticpages/admin/list.html'

    def get_context_data(self, **kwargs):
        ctx = super(AdminTemplateView, self).get_context_data(**kwargs)
        ctx.update({
            'legalpages': LegalPage.objects.all(),
        })
        return ctx


class PageCreateView(SuperuserRequiredMixin, PageModelMixin, CreateView):

    success_url = reverse_lazy('staticpages.admin')
    template_name = 'staticpages/admin/legalpage_create.html'


class PageUpdateView(SuperuserRequiredMixin, PageModelMixin, UpdateView):

    success_url = reverse_lazy('staticpages.admin')
    template_name = 'staticpages/admin/legalpage_update.html'

    def get_context_data(self, **kwargs):
        ctx = super(PageUpdateView, self).get_context_data(**kwargs)
        ctx.update({
            'show_delete': True,
        })
        return ctx


def page(request, virtual_path):
    """Returns an active page defined in `virtual_path`."""
    page = None
    for page_model in AbstractPage.__subclasses__():
        try:
            page = page_model.objects.get(
                    active=True,
                    virtual_path=virtual_path,
                )
        except ObjectDoesNotExist:
            pass

    if page is None:
        raise Http404

    if page.url:
        return redirect(page.url)

    template_name = 'staticpages/page.html'
    if 'HTTP_X_FANCYBOX' in request.META:
        template_name = 'staticpages/_body.html'

    return render_to_response(template_name, {'page': page},
                              RequestContext(request))
