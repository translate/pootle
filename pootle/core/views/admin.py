# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.urls import reverse
from django.views.generic import FormView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from pootle.core.views.mixins import SuperuserRequiredMixin

from .decorators import requires_permission, set_permissions


class PootleFormView(FormView):

    @property
    def success_kwargs(self):
        return {}

    @property
    def success_url(self):
        return reverse(
            self.success_url_pattern,
            kwargs=self.success_kwargs)

    def form_valid(self, form):
        if form.should_save():
            form.save()
            self.add_success_message(form)
            return super(PootleFormView, self).form_valid(form)
        return self.render_to_response(self.get_context_data(form=form))

    def add_success_message(self, form):
        pass


class PootleAddView(CreateView):

    @set_permissions
    @requires_permission("addproject")
    def dispatch(self, request, *args, **kwargs):
        return super(PootleAddView, self).dispatch(request, *args, **kwargs)


class PootleEditView(UpdateView):

    @set_permissions
    @requires_permission("editproject")
    def dispatch(self, request, *args, **kwargs):
        return super(PootleEditView, self).dispatch(request, *args, **kwargs)


class PootleAdminView(SuperuserRequiredMixin, TemplateView):
    pass


class PootleAdminFormView(SuperuserRequiredMixin, PootleFormView):
    pass
