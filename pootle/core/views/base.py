# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.views.decorators.cache import never_cache
from django.views.generic import DetailView

from pootle.core.url_helpers import get_path_parts
from pootle_app.models.permissions import check_permission
from pootle_misc.util import ajax_required

from .decorators import requires_permission, set_permissions
from .mixins import GatherContextMixin, PootleJSONMixin


class PootleDetailView(GatherContextMixin, DetailView):
    translate_url_path = ""
    browse_url_path = ""
    resource_path = ""
    view_name = ""

    @property
    def browse_url(self):
        return reverse(
            self.browse_url_path,
            kwargs=self.url_kwargs)

    @property
    def cache_key(self):
        return (
            "%s.%s.%s.%s"
            % (self.page_name,
               self.view_name,
               self.object.data_tool.cache_key,
               self.request_lang))

    @property
    def request_lang(self):
        return get_language()

    @cached_property
    def has_admin_access(self):
        return check_permission('administrate', self.request)

    @property
    def language(self):
        if self.tp:
            return self.tp.language

    @property
    def permission_context(self):
        return self.get_object()

    @property
    def pootle_path(self):
        return self.object.pootle_path

    @property
    def project(self):
        if self.tp:
            return self.tp.project

    @property
    def tp(self):
        return None

    @property
    def translate_url(self):
        return reverse(
            self.translate_url_path,
            kwargs=self.url_kwargs)

    @set_permissions
    @requires_permission("view")
    def dispatch(self, request, *args, **kwargs):
        # get funky with the request 8/
        return super(PootleDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        return {
            'object': self.object,
            'pootle_path': self.pootle_path,
            'project': self.project,
            'language': self.language,
            'translation_project': self.tp,
            'has_admin_access': self.has_admin_access,
            'resource_path': self.resource_path,
            'resource_path_parts': get_path_parts(self.resource_path),
            'translate_url': self.translate_url,
            'browse_url': self.browse_url,
            'unit_api_root': "/xhr/units/"}


class PootleJSON(PootleJSONMixin, PootleDetailView):

    @never_cache
    @method_decorator(ajax_required)
    @set_permissions
    @requires_permission("view")
    def dispatch(self, request, *args, **kwargs):
        return super(PootleJSON, self).dispatch(request, *args, **kwargs)


class PootleAdminView(DetailView):

    @set_permissions
    @requires_permission("administrate")
    def dispatch(self, request, *args, **kwargs):
        return super(PootleAdminView, self).dispatch(request, *args, **kwargs)

    @property
    def permission_context(self):
        return self.get_object().directory

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)
