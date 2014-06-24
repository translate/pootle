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

import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import ObjectDoesNotExist
from django.forms.models import modelform_factory
from django.http import Http404, HttpResponse
from django.template import loader, RequestContext
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View

from pootle_misc.util import PootleJSONEncoder, ajax_required, jsonify


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
        can_access = user.is_superuser or str(field_value) == url_field_value

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

    # Optional form template (and its context) to return for single object
    # requests
    edit_form_template = None
    edit_form_ctx = None

    # Tuple of sensitive field names that will be excluded from any
    # serialized responses
    sensitive_field_names = ('password', 'pw')

    # Set to an integer to enable GET pagination
    page_size = None

    # HTTP GET parameter to use for accessing pages
    page_param_name = 'p'

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
            qs.delete()
            return self.json_response(output)

        raise Http404

    def serialize_qs(self, queryset, single_object=False):
        """Serialize a queryset into a JSON object.

        :param single_object: if `True` (or the URL specified an id), it
            will return a single JSON object. Note that if
            `self.edit_form_template` is set, the response will include
            the edit form rendered as HTML.  If `False`, a JSON array of
            objects is returned otherwise.
        """
        values = queryset.values(*self.serialize_fields)

        if single_object or self.kwargs.get(self.pk_field_name):
            # For single-item requests, convert ValuesQueryset to a dict simply
            # by slicing the first item
            instance_values = values[0]

            if (self.edit_form_class is not None and
                self.edit_form_template is not None):
                # Create fake model instance to feed the form
                instance = self.model(**instance_values)
                form = self.edit_form_class(instance=instance)
                tpl = loader.get_template(self.edit_form_template)
                ctx = {'form': form}
                ctx.update(self.edit_form_ctx or {})
                html_form = tpl.render(RequestContext(self.request, ctx))

                serialize_values = {
                    'model': instance_values,
                    'form': html_form,
                }
            else:
                serialize_values = instance_values
        else:
            # Process pagination options if they are enabled
            if isinstance(self.page_size, int):
                try:
                    page_param = self.request.GET.get(self.page_param_name, 1)
                    page_number = int(page_param)
                    offset = (page_number - 1) * self.page_size
                except ValueError:
                    offset = 0

                values = values[offset:offset+self.page_size]

            serialize_values = list(values)

        return self.json_encoder.encode(serialize_values)

    def status_msg(self, msg, status=400):
        data = self.json_encoder.encode({'msg': msg})
        return self.json_response(data, status=status)

    def form_invalid(self, form):
        data = self.json_encoder.encode({'errors': form.errors})
        return self.json_response(data, status=400)

    def json_response(self, output, **response_kwargs):
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(output, **response_kwargs)
