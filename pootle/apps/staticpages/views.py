#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

from django.contrib import auth, messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse_lazy
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import loader, RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (CreateView, DeleteView, TemplateView,
                                  UpdateView)

from pootle.core.views import SuperuserRequiredMixin
from pootle_misc.baseurl import redirect
from pootle_misc.util import ajax_required, jsonify

from .forms import agreement_form_factory
from .models import AbstractPage, LegalPage, StaticPage


class PageModelMixin(object):
    """Mixin used to set the view's page model according to the
    `page_type` argument caught in a url pattern.
    """

    def dispatch(self, request, *args, **kwargs):
        self.page_type = kwargs.get('page_type', None)
        self.model = {
            'legal': LegalPage,
            'static': StaticPage,
        }.get(self.page_type)

        if self.model is None:
            raise Http404

        return super(PageModelMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(PageModelMixin, self).get_context_data(**kwargs)
        ctx.update({
            'has_page_model': True,
        })
        return ctx


class AdminTemplateView(SuperuserRequiredMixin, TemplateView):

    template_name = 'staticpages/admin/page_list.html'

    def get_context_data(self, **kwargs):
        ctx = super(AdminTemplateView, self).get_context_data(**kwargs)
        ctx.update({
            'legalpages': LegalPage.objects.all(),
            'staticpages': StaticPage.objects.all(),
        })
        return ctx


class PageCreateView(SuperuserRequiredMixin, PageModelMixin, CreateView):

    success_url = reverse_lazy('staticpages.admin')
    template_name = 'staticpages/admin/page_create.html'

    def get_initial(self):
        initial = super(PageModelMixin, self).get_initial()
        next_page_number = AbstractPage.max_pk() + 1
        initial.update({
            'title': _('Page Title'),
            'virtual_path': _('page-%d', next_page_number),
        })
        return initial


class PageUpdateView(SuperuserRequiredMixin, PageModelMixin, UpdateView):

    success_url = reverse_lazy('staticpages.admin')
    template_name = 'staticpages/admin/page_update.html'

    def get_context_data(self, **kwargs):
        ctx = super(PageUpdateView, self).get_context_data(**kwargs)
        ctx.update({
            'show_delete': True,
            'page_type': self.page_type,
        })
        return ctx


class PageDeleteView(SuperuserRequiredMixin, PageModelMixin, DeleteView):

    success_url = reverse_lazy('staticpages.admin')


def display_page(request, virtual_path):
    """Displays an active page defined in `virtual_path`."""
    page = None
    for page_model in AbstractPage.__subclasses__():
        try:
            page = page_model.objects.live(request.user).get(
                    virtual_path=virtual_path,
                )
        except ObjectDoesNotExist:
            pass

    if page is None:
        raise Http404

    if page.url:
        return redirect(page.url)

    if request.user.is_superuser and not page.active:
        msg = _('This page is inactive and visible to administrators '
                'only. You can activate it by <a href="%s">editing its '
                'properties</a>', page.get_edit_url())
        messages.warning(request, msg)

    template_name = 'staticpages/page_display.html'
    if request.is_ajax():
        template_name = 'staticpages/_body.html'

    ctx = {
        'page': page,
    }
    return render_to_response(template_name, ctx, RequestContext(request))


@ajax_required
def legal_agreement(request):
    """Displays the pending documents to be agreed by the current user."""
    pending_pages = LegalPage.objects.pending_user_agreement(request.user)
    form_class = agreement_form_factory(pending_pages, request.user)

    rcode = 200
    agreed = False

    if request.method == 'POST':
        form = form_class(request.POST)

        if form.is_valid():
            # The user agreed, let's record the specific agreements
            agreed = True
            form.save()
        else:
            rcode = 400
    else:
        form = form_class()

    response = {'agreed': agreed}
    if not agreed:
        ctx = {
            'form': form,
        }
        template = loader.get_template('staticpages/agreement.html')
        response['form'] = template.render(RequestContext(request, ctx))

    return HttpResponse(jsonify(response), status=rcode,
                        mimetype='application/json')
