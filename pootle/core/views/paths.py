# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import FormView

from pootle.core.exceptions import Http400
from pootle.core.forms import PathsSearchForm
from pootle_misc.util import ajax_required

from .decorators import requires_permission, set_permissions
from .mixins import PootleJSONMixin


class PootlePathsJSON(PootleJSONMixin, FormView):
    form_class = PathsSearchForm

    @never_cache
    @method_decorator(ajax_required)
    @set_permissions
    @requires_permission("view")
    def dispatch(self, request, *args, **kwargs):
        return super(PootlePathsJSON, self).dispatch(request, *args, **kwargs)

    @property
    def permission_context(self):
        return self.context.directory

    def get_context_data(self, **kwargs):
        context = super(PootlePathsJSON, self).get_context_data(**kwargs)
        form = context["form"]
        return (
            dict(items=form.search(show_all=self.request.user.is_superuser))
            if form.is_valid()
            else dict(items=[]))

    def get_form_kwargs(self):
        kwargs = super(PootlePathsJSON, self).get_form_kwargs()
        kwargs["data"] = self.request.POST
        kwargs["context"] = self.context
        return kwargs

    def form_valid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form))

    def form_invalid(self, form):
        raise Http400(form.errors)
