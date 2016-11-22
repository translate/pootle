# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.decorators import method_decorator

from pootle.core.delegate import context_data
from pootle.i18n.gettext import ugettext as _

from ..http import JsonResponse, JsonResponseBadRequest


class SuperuserRequiredMixin(object):
    """Require users to have the `is_superuser` bit set."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            msg = _('You do not have rights to administer Pootle.')
            raise PermissionDenied(msg)

        return super(SuperuserRequiredMixin, self).dispatch(request, *args,
                                                            **kwargs)


class UserObjectMixin(object):
    """Generic field definitions to be reused across user views."""

    context_object_name = 'object'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    @property
    def model(self):
        return get_user_model()


class TestUserFieldMixin(object):
    """Require a field from the URL pattern to match a field of the
    current user.

    The URL pattern field used for comparing against the current user
    can be customized by setting the `username_field` attribute.

    Note that there's free way for admins.
    """

    test_user_field = 'username'

    @method_decorator(login_required)
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


class GatherContextMixin(object):

    def gather_context_data(self, context):
        context.update(
            context_data.gather(
                sender=self.__class__,
                context=context, view=self))
        return context

    def render_to_response(self, context, **response_kwargs):
        return super(GatherContextMixin, self).render_to_response(
            self.gather_context_data(context),
            **response_kwargs)


class PootleJSONMixin(GatherContextMixin):

    response_class = JsonResponse

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
