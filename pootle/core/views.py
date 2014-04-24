#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _

from pootle_misc.util import ajax_required, jsonify


class SuperuserRequiredMixin(object):
    """Require users to have the `is_superuser` bit set."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            msg = _('You do not have rights to administer Pootle.')
            raise PermissionDenied(msg)

        return super(SuperuserRequiredMixin, self) \
                .dispatch(request, *args, **kwargs)


class LoginRequiredMixin(object):
    """Require a logged-in user."""
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class AjaxResponseMixin(object):
    """Mixin to add AJAX support to a form."""
    @method_decorator(ajax_required)
    def dispatch(self, *args, **kwargs):
        return super(AjaxResponseMixin, self).dispatch(*args, **kwargs)

    def render_to_json_response(self, context, **response_kwargs):
        data = jsonify(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def form_invalid(self, form):
        response = super(AjaxResponseMixin, self).form_invalid(form)
        return self.render_to_json_response(form.errors, status=400)

    def form_valid(self, form):
        response = super(AjaxResponseMixin, self).form_valid(form)
        return self.render_to_json_response({})
