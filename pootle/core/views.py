#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
import operator

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import ObjectDoesNotExist, ProtectedError, Q
from django.forms.models import modelform_factory
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.defaults import (permission_denied as django_403,
                                   page_not_found as django_404,
                                   server_error as django_500)
from django.views.generic import View

from .http import JsonResponse, JsonResponseBadRequest
from .utils.json import PootleJSONEncoder


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


class TestUserFieldMixin(LoginRequiredMixin):
    """Require a field from the URL pattern to match a field of the
    current user.

    The URL pattern field used for comparing against the current user
    can be customized by setting the `username_field` attribute.

    Note that there's free way for admins.
    """
    test_user_field = 'username'

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        url_field_value = kwargs[self.test_user_field]
        field_value = getattr(user, self.test_user_field, '')
        can_access = user.is_superuser or unicode(field_value) == url_field_value

        if not can_access:
            raise PermissionDenied(_('You cannot access this page.'))

        return super(TestUserFieldMixin, self).dispatch(*args, **kwargs)


class NoDefaultUserMixin(object):
    """Removes the `default` special user from views."""
    def dispatch(self, request, *args, **kwargs):
        username = kwargs.get('username', None)
        if username is not None and username == 'default':
            raise Http404

        return super(NoDefaultUserMixin, self) \
            .dispatch(request, *args, **kwargs)


class AjaxResponseMixin(object):
    """Mixin to add AJAX support to a form.

    This needs to be used with a `FormView`.
    """
    def form_invalid(self, form):
        super(AjaxResponseMixin, self).form_invalid(form)
        return JsonResponseBadRequest({'errors': form.errors})

    def form_valid(self, form):
        super(AjaxResponseMixin, self).form_valid(form)
        return JsonResponse({})


class APIView(View):
    """View to implement internal RESTful APIs.

    Based on djangbone https://github.com/af/djangbone
    """
    # Model on which this view operates. Setting this is required
    model = None

    # Base queryset for accessing data. If `None`, model's default manager
    # will be used
    base_queryset = None

    # Set this to restrict the view to a subset of the available methods
    restrict_to_methods = None

    # Field names to be included
    fields = ()

    # Individual forms to use for each method. By default it'll
    # auto-populate model forms built using `self.model` and `self.fields`
    add_form_class = None
    edit_form_class = None

    # Tuple of sensitive field names that will be excluded from any
    # serialized responses
    sensitive_field_names = ('password', 'pw')

    # Set to an integer to enable GET pagination
    page_size = None

    # HTTP GET parameter to use for accessing pages
    page_param_name = 'p'

    # HTTP GET parameter to use for search queries
    search_param_name = 'q'

    # Field names in which searching will be allowed
    search_fields = None

    # Override these if you have custom JSON encoding/decoding needs
    json_encoder = PootleJSONEncoder()
    json_decoder = json.JSONDecoder()

    @property
    def allowed_methods(self):
        methods = [m for m in self.http_method_names if hasattr(self, m)]

        if self.restrict_to_methods is not None:
            restricted_to = map(lambda x: x.lower(), self.restrict_to_methods)
            methods = filter(lambda x: x in restricted_to, methods)

        return methods

    def __init__(self, *args, **kwargs):
        if self.model is None:
            raise ValueError('No model class specified.')

        self.pk_field_name = self.model._meta.pk.name

        if self.base_queryset is None:
            self.base_queryset = self.model._default_manager

        self._init_fields()
        self._init_forms()

        return super(APIView, self).__init__(*args, **kwargs)

    def _init_fields(self):
        if len(self.fields) < 1:
            form = self.add_form_class or self.edit_form_class
            if form is not None:
                self.fields = form._meta.fields
            else:  # Assume all fields by default
                self.fields = (f.name for f in self.model._meta.fields)

        self.serialize_fields = (f for f in self.fields if
                                 f not in self.sensitive_field_names)

    def _init_forms(self):
        if 'post' in self.allowed_methods and self.add_form_class is None:
            self.add_form_class = modelform_factory(self.model,
                                                    fields=self.fields)

        if 'put' in self.allowed_methods and self.edit_form_class is None:
            self.edit_form_class = modelform_factory(self.model,
                                                     fields=self.fields)

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in self.allowed_methods:
            handler = getattr(self, request.method.lower(),
                              self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        return handler(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """GET handler."""
        if kwargs.get(self.pk_field_name, None) is not None:
            return self.get_single_item(request, *args, **kwargs)

        return self.get_collection(request, *args, **kwargs)

    def get_single_item(self, request, *args, **kwargs):
        """Returns a single model instance."""
        try:
            qs = self.base_queryset.filter(pk=kwargs[self.pk_field_name])
            assert len(qs) == 1
        except AssertionError:
            raise Http404

        return self.json_response(self.serialize_qs(qs))

    def get_collection(self, request, *args, **kwargs):
        """Retrieve a full collection."""
        return self.json_response(self.serialize_qs(self.base_queryset))

    def post(self, request, *args, **kwargs):
        """Creates a new model instance.

        The form to be used can be customized by setting
        `self.add_form_class`. By default a model form will be used with
        the fields from `self.fields`.
        """
        try:
            request_dict = self.json_decoder.decode(request.body)
        except ValueError:
            return self.status_msg('Invalid JSON data', status=400)

        form = self.add_form_class(request_dict)

        if form.is_valid():
            new_object = form.save()
            # Serialize the new object to json using our built-in methods.
            # The extra DB read here is not ideal, but it keeps the code
            # DRY:
            wrapper_qs = self.base_queryset.filter(pk=new_object.pk)
            return self.json_response(
                self.serialize_qs(wrapper_qs, single_object=True)
            )

        return self.form_invalid(form)

    def put(self, request, *args, **kwargs):
        """Update the current model."""
        if self.pk_field_name not in kwargs:
            return self.status_msg('PUT is not supported for collections',
                                   status=405)

        try:
            request_dict = self.json_decoder.decode(request.body)
            instance = self.base_queryset.get(pk=kwargs[self.pk_field_name])
        except ValueError:
            return self.status_msg('Invalid JSON data', status=400)
        except ObjectDoesNotExist:
            raise Http404

        form = self.edit_form_class(request_dict, instance=instance)

        if form.is_valid():
            item = form.save()
            wrapper_qs = self.base_queryset.filter(id=item.id)
            return self.json_response(
                self.serialize_qs(wrapper_qs, single_object=True)
            )

        return self.form_invalid(form)

    def delete(self, request, *args, **kwargs):
        """Delete the model and return its JSON representation."""
        if self.pk_field_name not in kwargs:
            return self.status_msg('DELETE is not supported for collections',
                                   status=405)

        qs = self.base_queryset.filter(id=kwargs[self.pk_field_name])
        if qs:
            output = self.serialize_qs(qs)
            obj = qs[0]
            try:
                obj.delete()
                return self.json_response(output)
            except ProtectedError as e:
                return self.status_msg(e[0], status=405)

        raise Http404

    def serialize_qs(self, queryset, single_object=False):
        """Serialize a queryset into a JSON object.

        :param single_object: if `True` (or the URL specified an id), it
            will return a single JSON object.
            If `False`, a JSON object is returned with an array of objects
            in `models` and the total object count in `count`.
        """
        if single_object or self.kwargs.get(self.pk_field_name):
            values = queryset.values(*self.serialize_fields)
            # For single-item requests, convert ValuesQueryset to a dict simply
            # by slicing the first item
            serialize_values = values[0]
        else:
            search_keyword = self.request.GET.get(self.search_param_name, None)
            if search_keyword is not None:
                filter_by = self.get_search_filter(search_keyword)
                queryset = queryset.filter(filter_by)

            values = queryset.values(*self.serialize_fields)

            # Process pagination options if they are enabled
            if isinstance(self.page_size, int):
                try:
                    page_param = self.request.GET.get(self.page_param_name, 1)
                    page_number = int(page_param)
                    offset = (page_number - 1) * self.page_size
                except ValueError:
                    offset = 0

                values = values[offset:offset+self.page_size]

            serialize_values = {
                'models': list(values),
                'count': queryset.count(),
            }

        return self.json_encoder.encode(serialize_values)

    def get_search_filter(self, keyword):
        search_fields = getattr(self, 'search_fields', None)
        if search_fields is None:
            search_fields = self.fields  # Assume all fields

        field_queries = list(
            zip(map(lambda x: '%s__icontains' % x, search_fields),
                (keyword,)*len(search_fields))
        )
        lookups = [Q(x) for x in field_queries]

        return reduce(operator.or_, lookups)

    def status_msg(self, msg, status=400):
        data = self.json_encoder.encode({'msg': msg})
        return self.json_response(data, status=status)

    def form_invalid(self, form):
        data = self.json_encoder.encode({'errors': form.errors})
        return self.json_response(data, status=400)

    def json_response(self, output, **response_kwargs):
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(output, **response_kwargs)


def permission_denied(request):
    return django_403(request, template_name='errors/403.html')


def page_not_found(request):
    return django_404(request, template_name='errors/404.html')


def server_error(request):
    return django_500(request, template_name='errors/500.html')
