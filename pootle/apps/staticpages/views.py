#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse_lazy
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template import loader, RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (CreateView, DeleteView, TemplateView,
                                  UpdateView)

from pootle.core.views import SuperuserRequiredMixin
from pootle_misc.util import ajax_required, jsonify

from .forms import agreement_form_factory
from .models import AbstractPage, LegalPage, StaticPage


ANN_TYPE = u'announcements'
ANN_VPATH = ANN_TYPE + u'/'


class PageModelMixin(object):
    """Mixin used to set the view's page model according to the
    `page_type` argument caught in a url pattern.
    """

    def dispatch(self, request, *args, **kwargs):
        self.page_type = kwargs.get('page_type', None)
        self.model = {
            'legal': LegalPage,
            'static': StaticPage,
            ANN_TYPE: StaticPage,
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

    def get_form(self, form_class):
        form = super(PageModelMixin, self).get_form(form_class)

        if self.page_type == ANN_TYPE:
            form.fields['virtual_path'].help_text = u'/pages/' + ANN_VPATH

        return form

    def form_valid(self, form):
        if (self.page_type == ANN_TYPE and not
            form.cleaned_data['virtual_path'].startswith(ANN_VPATH)):
            orig_vpath = form.cleaned_data['virtual_path']
            form.instance.virtual_path = ANN_VPATH + orig_vpath

        return super(PageModelMixin, self).form_valid(form)


class AdminTemplateView(SuperuserRequiredMixin, TemplateView):

    template_name = 'admin/staticpages/page_list.html'

    def get_context_data(self, **kwargs):
        legal_pages = LegalPage.objects.all()
        static_pages = StaticPage.objects.exclude(
            virtual_path__startswith=ANN_VPATH,
        )
        announcements = StaticPage.objects.filter(
            virtual_path__startswith=ANN_VPATH,
        )

        ctx = super(AdminTemplateView, self).get_context_data(**kwargs)
        ctx.update({
            'legalpages': legal_pages,
            'staticpages': static_pages,
            ANN_TYPE: announcements,
        })
        return ctx


class PageCreateView(SuperuserRequiredMixin, PageModelMixin, CreateView):

    success_url = reverse_lazy('pootle-staticpages')
    template_name = 'admin/staticpages/page_create.html'

    def get_initial(self):
        initial = super(PageModelMixin, self).get_initial()

        initial_args = {
            'title': _('Page Title'),
        }

        if self.page_type != ANN_TYPE:
            next_page_number = AbstractPage.max_pk() + 1
            initial_args['virtual_path'] = _('page-%d', next_page_number)

        initial.update(initial_args)

        return initial

    def get_form(self, form_class):
        form = super(PageCreateView, self).get_form(form_class)

        if self.page_type == ANN_TYPE:
            del form.fields['url']
            form.fields['virtual_path'] \
                .widget.attrs['placeholder'] = u'projects/<project_code>'

        return form


class PageUpdateView(SuperuserRequiredMixin, PageModelMixin, UpdateView):

    success_url = reverse_lazy('pootle-staticpages')
    template_name = 'admin/staticpages/page_update.html'

    def get_context_data(self, **kwargs):
        ctx = super(PageUpdateView, self).get_context_data(**kwargs)
        ctx.update({
            'show_delete': True,
            'page_type': self.page_type,
        })
        return ctx

    def get_form_kwargs(self):
        kwargs = super(PageUpdateView, self).get_form_kwargs()

        if self.page_type == ANN_TYPE:
            orig_vpath = self.object.virtual_path
            self.object.virtual_path = orig_vpath.replace(ANN_VPATH, '')
            kwargs.update({'instance': self.object})

        return kwargs


class PageDeleteView(SuperuserRequiredMixin, PageModelMixin, DeleteView):

    success_url = reverse_lazy('pootle-staticpages')


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
    return render(request, template_name, ctx)


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
                        content_type='application/json')
