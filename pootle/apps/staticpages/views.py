# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, TemplateView,
                                  UpdateView)

from pootle.core.http import JsonResponse, JsonResponseBadRequest
from pootle.core.markup.filters import apply_markup_filter
from pootle.core.views.mixins import SuperuserRequiredMixin
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_misc.util import ajax_required

from .forms import agreement_form_factory
from .models import ANN_TYPE, ANN_VPATH, AbstractPage, LegalPage, StaticPage


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
            'page_display_name': self.model.display_name,
        })
        return ctx

    def get_form_kwargs(self):
        kwargs = super(PageModelMixin, self).get_form_kwargs()
        kwargs.update({'label_suffix': ''})
        return kwargs

    def get_form(self, form_class=None):
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


class AdminCtxMixin(object):

    def get_context_data(self, **kwargs):
        ctx = super(AdminCtxMixin, self).get_context_data(**kwargs)
        ctx.update({
            'page': 'admin-pages',
        })
        return ctx


class AdminTemplateView(SuperuserRequiredMixin, AdminCtxMixin, TemplateView):

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


class PageCreateView(SuperuserRequiredMixin, AdminCtxMixin, PageModelMixin,
                     CreateView):
    fields = ('title', 'virtual_path', 'active', 'url', 'body')

    success_url = reverse_lazy('pootle-staticpages')
    template_name = 'admin/staticpages/page_create.html'

    def get_initial(self):
        initial = super(PageModelMixin, self).get_initial()

        initial_args = {
            'title': _('Page Title'),
        }

        if self.page_type != ANN_TYPE:
            next_page_number = AbstractPage.max_pk() + 1
            initial_args['virtual_path'] = 'page-%d' % next_page_number

        initial.update(initial_args)

        return initial

    def get_form(self, form_class=None):
        form = super(PageCreateView, self).get_form(form_class)

        if self.page_type == ANN_TYPE:
            del form.fields['url']
            # Translators: 'projects' must not be translated.
            msg = _(u'projects/<project_code> or <language_code> or '
                    u'<language_code>/<project_code>')
            form.fields['virtual_path'].widget.attrs['placeholder'] = msg
            form.fields['virtual_path'].widget.attrs['size'] = 100

        return form


class PageUpdateView(SuperuserRequiredMixin, AdminCtxMixin, PageModelMixin,
                     UpdateView):
    fields = ('title', 'virtual_path', 'active', 'url', 'body')

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
            page = page_model.objects.live(
                request.user).get(virtual_path=virtual_path,)
        except ObjectDoesNotExist:
            pass

    if page is None:
        raise Http404

    if page.url:
        return redirect(page.url)

    template_name = 'staticpages/page_display.html'
    if request.is_ajax():
        template_name = 'staticpages/_body.html'

    ctx = {
        'page': page,
    }
    return render(request, template_name, ctx)


def _get_rendered_agreement(request, form):
    template = get_template('staticpages/agreement.html')
    return template.render(context={'form': form}, request=request)


@ajax_required
def legal_agreement(request):
    """Displays the pending documents to be agreed by the current user."""
    pending_pages = LegalPage.objects.pending_user_agreement(request.user)
    form_class = agreement_form_factory(pending_pages, request.user)

    if request.method == 'POST':
        form = form_class(request.POST)

        if form.is_valid():
            form.save()
            return JsonResponse({})

        rendered_form = _get_rendered_agreement(request, form)
        return JsonResponseBadRequest({'form': rendered_form})

    rendered_form = _get_rendered_agreement(request, form_class())
    return JsonResponse({'form': rendered_form})


@ajax_required
def preview_content(request):
    """Returns content rendered based on the configured markup settings."""
    if 'text' not in request.POST:
        return JsonResponseBadRequest({
            'msg': _('Text is missing'),
        })

    return JsonResponse({
        'rendered': apply_markup_filter(request.POST['text']),
    })
