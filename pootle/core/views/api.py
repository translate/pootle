# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
import operator

from django.db.models import ObjectDoesNotExist, ProtectedError, Q
from django.forms.models import modelform_factory
from django.http import Http404
from django.views.generic import View

from pootle.core.http import JsonResponse


class APIView(View):
    """View to implement internal RESTful APIs.

    Based on djangbone https://github.com/af/djangbone
    """

    # Model on which this view operates. Setting this is required
    model = None

    # Base queryset for accessing data. If `None`, model's default manager will
    # be used
    base_queryset = None

    # Set this to restrict the view to a subset of the available methods
    restrict_to_methods = None

    # Field names to be included
    fields = ()

    # Individual forms to use for each method. By default it'll auto-populate
    # model forms built using `self.model` and `self.fields`
    add_form_class = None
    edit_form_class = None

    # Tuple of sensitive field names that will be excluded from any serialized
    # responses
    sensitive_field_names = ('password', 'pw')

    # Set to an integer to enable GET pagination
    page_size = None

    # HTTP GET parameter to use for accessing pages
    page_param_name = 'p'

    # HTTP GET parameter to use for search queries
    search_param_name = 'q'

    # Field names in which searching will be allowed
    search_fields = None

    m2m = ()

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

        return JsonResponse(self.qs_to_values(qs))

    def get_collection(self, request, *args, **kwargs):
        """Retrieve a full collection."""
        return JsonResponse(self.qs_to_values(self.base_queryset))

    def post(self, request, *args, **kwargs):
        """Creates a new model instance.

        The form to be used can be customized by setting
        `self.add_form_class`. By default a model form will be used with
        the fields from `self.fields`.
        """
        try:
            request_dict = json.loads(request.body)
        except ValueError:
            return self.status_msg('Invalid JSON data', status=400)

        form = self.add_form_class(request_dict)

        if form.is_valid():
            new_object = form.save()
            # Serialize the new object to json using our built-in methods. The
            # extra DB read here is not ideal, but it keeps the code DRY:
            wrapper_qs = self.base_queryset.filter(pk=new_object.pk)
            return JsonResponse(
                self.qs_to_values(wrapper_qs, single_object=True)
            )

        return self.form_invalid(form)

    def put(self, request, *args, **kwargs):
        """Update the current model."""
        if self.pk_field_name not in kwargs:
            return self.status_msg('PUT is not supported for collections',
                                   status=405)

        try:
            request_dict = json.loads(request.body)
            instance = self.base_queryset.get(pk=kwargs[self.pk_field_name])
        except ValueError:
            return self.status_msg('Invalid JSON data', status=400)
        except ObjectDoesNotExist:
            raise Http404

        form = self.edit_form_class(request_dict, instance=instance)

        if form.is_valid():
            item = form.save()
            wrapper_qs = self.base_queryset.filter(id=item.id)
            return JsonResponse(
                self.qs_to_values(wrapper_qs, single_object=True)
            )

        return self.form_invalid(form)

    def delete(self, request, *args, **kwargs):
        """Delete the model and return its JSON representation."""
        if self.pk_field_name not in kwargs:
            return self.status_msg('DELETE is not supported for collections',
                                   status=405)

        qs = self.base_queryset.filter(id=kwargs[self.pk_field_name])
        if qs:
            output = self.qs_to_values(qs)
            obj = qs[0]
            try:
                obj.delete()
                return JsonResponse(output)
            except ProtectedError as e:
                return self.status_msg(e[0], status=405)

        raise Http404

    def serialize_m2m(self, info, item):
        for k in self.m2m:
            info[k] = [
                str(x) for x
                in getattr(item, k).values_list("pk", flat=True)]

    def qs_to_values(self, queryset, single_object=False):
        """Convert a queryset to values for further serialization.

        :param single_object: if `True` (or the URL specified an id), it
            will return a single element.
            If `False`, an array of objects in `models` and the total object
            count in `count` is returned.
        """

        if single_object or self.kwargs.get(self.pk_field_name):
            values = queryset.values(
                *[k for k in self.serialize_fields if k not in self.m2m])
            # For single-item requests, convert ValuesQueryset to a dict simply
            # by slicing the first item
            return_values = values[0]
            if self.m2m:
                self.serialize_m2m(return_values, queryset[0])
        else:
            search_keyword = self.request.GET.get(self.search_param_name, None)
            if search_keyword is not None:
                filter_by = self.get_search_filter(search_keyword)
                queryset = queryset.filter(filter_by)

            values = queryset.all()
            # Process pagination options if they are enabled
            if isinstance(self.page_size, int):
                try:
                    page_param = self.request.GET.get(self.page_param_name, 1)
                    page_number = int(page_param)
                    offset = (page_number - 1) * self.page_size
                except ValueError:
                    offset = 0
                values = values[offset:offset+self.page_size]
            # handle m2m fields
            if self.m2m:
                serialize_fields = set(self.serialize_fields)
                _serialize_fields = serialize_fields | set(["pk"])
                all_values = []
                # first retrieve the non-m2m fields
                field_values = {
                    x["pk"]: x
                    for x
                    in values.values(
                        *[k for k in _serialize_fields if k not in self.m2m])}
                # now add the m2m fields
                related_fields = values.prefetch_related(*self.m2m).iterator()
                for item in related_fields:
                    info = field_values[item.pk]
                    if "pk" not in serialize_fields:
                        del info["pk"]
                    self.serialize_m2m(info, item)
                    all_values.append(info)
                values = all_values
            else:
                values = values.values(*self.serialize_fields)

            return_values = {
                'models': list(values),
                'count': queryset.count(),
            }

        return return_values

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
        return JsonResponse({'msg': msg}, status=status)

    def form_invalid(self, form):
        return JsonResponse({'errors': form.errors}, status=400)
