# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools
from itertools import groupby
import json
import operator

from django.forms import ValidationError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import ObjectDoesNotExist, ProtectedError, Q
from django.forms.models import modelform_factory
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.defaults import (permission_denied as django_403,
                                   page_not_found as django_404,
                                   server_error as django_500)
from django.views.generic import View, DetailView

from pootle.core.delegate import search_backend, context_data
from pootle.core.url_helpers import split_pootle_path
from pootle_app.models.permissions import (
    check_permission, get_matching_permissions)
from pootle_misc.checks import get_qualitycheck_list, get_qualitycheck_schema
from pootle_misc.forms import make_search_form
from pootle_misc.util import ajax_required
from pootle_store.forms import UnitExportForm
from pootle_store.models import Unit

from .browser import get_table_headings
from .helpers import (SIDEBAR_COOKIE_NAME,
                      get_filter_name, get_sidebar_announcements_context)
from .http import JsonResponse, JsonResponseBadRequest
from .url_helpers import get_path_parts, get_previous_url
from .utils.json import PootleJSONEncoder
from .utils.stats import get_translation_states


def check_directory_permission(permission_codename, request, directory):
    """Checks if the current user has `permission_codename`
    permissions for a given directory.
    """
    if request.user.is_superuser:
        return True

    if permission_codename == 'view':
        context = None

        context = getattr(directory, "translation_project", None)
        if context is None:
            context = getattr(directory, "project", None)

        if context is None:
            return True

        return context.is_accessible_by(request.user)

    return (
        "administrate" in request.permissions
        or permission_codename in request.permissions)


def set_permissions(f):

    @functools.wraps(f)
    def method_wrapper(self, request, *args, **kwargs):
        request.permissions = get_matching_permissions(
            request.user,
            self.permission_context) or []
        return f(self, request, *args, **kwargs)
    return method_wrapper


def requires_permission(permission):

    def class_wrapper(f):

        @functools.wraps(f)
        def method_wrapper(self, request, *args, **kwargs):
            directory_permission = check_directory_permission(
                permission, request, self.permission_context)
            if not directory_permission:
                raise PermissionDenied(
                    _("Insufficient rights to access this page."), )
            return f(self, request, *args, **kwargs)
        return method_wrapper
    return class_wrapper


class SuperuserRequiredMixin(object):
    """Require users to have the `is_superuser` bit set."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            msg = _('You do not have rights to administer Pootle.')
            raise PermissionDenied(msg)

        return super(SuperuserRequiredMixin, self).dispatch(request, *args,
                                                            **kwargs)


class LoginRequiredMixin(object):
    """Require a logged-in user."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class UserObjectMixin(object):
    """Generic field definitions to be reused across user views."""

    model = get_user_model()
    context_object_name = 'object'
    slug_field = 'username'
    slug_url_kwarg = 'username'


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
        can_access = user.is_superuser or \
            unicode(field_value) == url_field_value

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
            # Serialize the new object to json using our built-in methods. The
            # extra DB read here is not ideal, but it keeps the code DRY:
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


class PootleAdminView(DetailView):

    @set_permissions
    @requires_permission("administrate")
    def dispatch(self, request, *args, **kwargs):
        return super(
            PootleAdminView, self).dispatch(request, *args, **kwargs)

    @property
    def permission_context(self):
        return self.get_object().directory

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)


class PootleDetailView(DetailView):
    translate_url_path = ""
    browse_url_path = ""
    export_url_path = ""
    resource_path = ""

    @property
    def browse_url(self):
        return reverse(
            self.browse_url_path,
            kwargs=self.url_kwargs)

    @property
    def export_url(self):
        return reverse(
            self.export_url_path,
            kwargs=self.url_kwargs)

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
            'export_url': self.export_url,
            'browse_url': self.browse_url}

    def gather_context_data(self, context):
        context.update(
            context_data.gather(
                sender=self.__class__,
                context=context, view=self))
        return context

    def render_to_response(self, context, **response_kwargs):
        return super(PootleDetailView, self).render_to_response(
            self.gather_context_data(context),
            **response_kwargs)


class PootleJSON(PootleDetailView):

    response_class = JsonResponse

    @never_cache
    @method_decorator(ajax_required)
    @set_permissions
    @requires_permission("view")
    def dispatch(self, request, *args, **kwargs):
        return super(PootleDetailView, self).dispatch(request, *args, **kwargs)

    def get_response_data(self, context):
        """Override this method if you need to render a template with the context object
        but wish to include the rendered output within a JSON response
        """
        return context

    def render_to_response(self, context, **response_kwargs):
        """Overriden to call `get_response_data` with output from
        `get_context_data`
        """
        response_kwargs.setdefault('content_type', self.content_type)
        return self.response_class(
            self.get_response_data(self.gather_context_data(context)),
            **response_kwargs)


class PootleBrowseView(PootleDetailView):
    template_name = 'browser/index.html'
    table_id = None
    table_fields = None
    items = None
    is_store = False

    @property
    def path(self):
        return self.request.path

    @property
    def stats(self):
        return self.object.get_stats()

    @property
    def has_vfolders(self):
        return False

    @cached_property
    def cookie_data(self):
        ctx, cookie_data = self.sidebar_announcements
        return cookie_data

    @property
    def sidebar_announcements(self):
        return get_sidebar_announcements_context(
            self.request,
            (self.object, ))

    @property
    def disabled_items(self):
        return filter(lambda item: item['is_disabled'], self.items)

    @property
    def table(self):
        if self.table_id and self.table_fields and self.items:
            return {
                'id': self.table_id,
                'fields': self.table_fields,
                'headings': get_table_headings(self.table_fields),
                'items': self.items,
                'disabled_items': self.disabled_items,
            }

    def get(self, *args, **kwargs):
        response = super(PootleBrowseView, self).get(*args, **kwargs)
        if self.cookie_data:
            response.set_cookie(
                SIDEBAR_COOKIE_NAME, self.cookie_data)
        return response

    def get_context_data(self, *args, **kwargs):
        filters = {}
        can_translate = False
        can_translate_stats = False
        User = get_user_model()
        if self.has_vfolders:
            filters['sort'] = 'priority'

        if self.request.user.is_superuser or self.language:
            can_translate = True
            can_translate_stats = True
            url_action_continue = self.object.get_translate_url(
                state='incomplete',
                **filters)
            url_action_fixcritical = self.object.get_critical_url(
                **filters)
            url_action_review = self.object.get_translate_url(
                state='suggestions',
                **filters)
            url_action_view_all = self.object.get_translate_url(state='all')
        else:
            if self.project:
                can_translate = True
            url_action_continue = None
            url_action_fixcritical = None
            url_action_review = None
            url_action_view_all = None
        ctx, cookie_data = self.sidebar_announcements
        ctx.update(
            super(PootleBrowseView, self).get_context_data(*args, **kwargs))

        language_code, project_code = split_pootle_path(self.pootle_path)[:2]

        ctx.update(
            {'page': 'browse',
             'stats': self.stats,
             'translation_states': get_translation_states(self.object),
             'checks': get_qualitycheck_list(self.object),
             'can_translate': can_translate,
             'can_translate_stats': can_translate_stats,
             'url_action_continue': url_action_continue,
             'url_action_fixcritical': url_action_fixcritical,
             'url_action_review': url_action_review,
             'url_action_view_all': url_action_view_all,
             'table': self.table,
             'is_store': self.is_store,
             'top_scorers': User.top_scorers(project=project_code,
                                             language=language_code,
                                             limit=10),
             'browser_extends': self.template_extends})
        return ctx


class PootleTranslateView(PootleDetailView):
    template_name = "editor/main.html"

    @property
    def ctx_path(self):
        return self.pootle_path

    @property
    def vfolder_pk(self):
        return ""

    @property
    def display_vfolder_priority(self):
        return False

    def get_context_data(self, *args, **kwargs):
        ctx = super(
            PootleTranslateView, self).get_context_data(*args, **kwargs)
        ctx.update(
            {'page': 'translate',
             'current_vfolder_pk': self.vfolder_pk,
             'ctx_path': self.ctx_path,
             'display_priority': self.display_vfolder_priority,
             'check_categories': get_qualitycheck_schema(),
             'cantranslate': check_permission("translate", self.request),
             'cansuggest': check_permission("suggest", self.request),
             'canreview': check_permission("review", self.request),
             'search_form': make_search_form(request=self.request),
             'previous_url': get_previous_url(self.request),
             'POOTLE_MT_BACKENDS': settings.POOTLE_MT_BACKENDS,
             'AMAGAMA_URL': settings.AMAGAMA_URL,
             'editor_extends': self.template_extends})
        return ctx


class PootleExportView(PootleDetailView):
    template_name = 'editor/export_view.html'

    @property
    def path(self):
        return self.request.path.replace("export-view/", "")

    def get_context_data(self, *args, **kwargs):
        ctx = {}
        filter_name, filter_extra = get_filter_name(self.request.GET)

        form_data = self.request.GET.copy()
        form_data["path"] = self.path

        search_form = UnitExportForm(
            form_data, user=self.request.user)

        if not search_form.is_valid():
            raise Http404(
                ValidationError(search_form.errors).messages)

        total, start, end, units_qs = search_backend.get(Unit)(
            self.request.user, **search_form.cleaned_data).search()

        units_qs = units_qs.select_related('store')

        if total > settings.POOTLE_EXPORT_VIEW_LIMIT:
            units_qs = units_qs[:settings.POOTLE_EXPORT_VIEW_LIMIT]
            ctx.update(
                {'unit_total_count': total,
                 'displayed_unit_count': settings.POOTLE_EXPORT_VIEW_LIMIT})

        unit_groups = [
            (path, list(units))
            for path, units
            in groupby(units_qs, lambda x: x.store.pootle_path)]

        ctx.update(
            {'unit_groups': unit_groups,
             'filter_name': filter_name,
             'filter_extra': filter_extra,
             'source_language': self.source_language,
             'language': self.language,
             'project': self.project})
        return ctx
