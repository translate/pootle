# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from __future__ import print_function

import sys
import traceback

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_admins
from django.http import Http404, HttpResponseForbidden, HttpResponseServerError
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import force_text

try:
    from raven.contrib.django.models import sentry_exception_handler
except ImportError:
    sentry_exception_handler = None

from pootle.core.exceptions import Http400
from pootle.core.http import (JsonResponseBadRequest, JsonResponseForbidden,
                              JsonResponseNotFound, JsonResponseServerError)
from pootle.i18n.gettext import ugettext as _


def log_exception(request, exception, tb):
    if sentry_exception_handler is None:
        # Send email to admins with details about exception
        ip_type = (request.META.get('REMOTE_ADDR') in
                   settings.INTERNAL_IPS and 'internal' or
                   'EXTERNAL')
        msg_args = {
            'ip_type': ip_type,
            'path': request.path,
        }
        subject = 'Error (%(ip_type)s IP): %(path)s' % msg_args

        try:
            request_repr = repr(request)
        except:
            request_repr = "Request repr() unavailable"

        msg_args = (unicode(exception.args[0]), tb,
                    request_repr)
        message = "%s\n\n%s\n\n%s" % msg_args
        mail_admins(subject, message, fail_silently=True)
    else:
        sentry_exception_handler(request=request)


def handle_exception(request, exception, template_name):
    # XXX: remove this? exceptions are already displayed in debug mode
    tb = traceback.format_exc()
    print(tb, file=sys.stderr)

    if settings.DEBUG:
        return None

    try:
        log_exception(request, exception, tb)

        msg = force_text(exception)

        if request.is_ajax():
            return JsonResponseServerError({'msg': msg})

        ctx = {
            'exception': msg,
        }
        if hasattr(exception, 'filename'):
            msg_args = {
                'filename': exception.filename,
                'errormsg': exception.strerror,
            }
            msg = _('Error accessing %(filename)s, Filesystem '
                    'sent error: %(errormsg)s', msg_args)
            ctx['fserror'] = msg

        return HttpResponseServerError(
            render_to_string(template_name, context=ctx, request=request)
        )
    except:
        # Let's not confuse things by throwing an exception here
        pass


class ErrorPagesMiddleware(MiddlewareMixin):
    """Friendlier error pages."""

    def process_exception(self, request, exception):
        msg = force_text(exception)
        if isinstance(exception, Http404):
            if request.is_ajax():
                return JsonResponseNotFound({'msg': msg})
        elif isinstance(exception, Http400):
            if request.is_ajax():
                return JsonResponseBadRequest({'msg': msg})
        elif isinstance(exception, PermissionDenied):
            if request.is_ajax():
                return JsonResponseForbidden({'msg': msg})

            ctx = {
                'permission_error': msg,
            }

            if not request.user.is_authenticated:
                msg_args = {
                    'login_link': reverse('account_login'),
                }
                login_msg = _(
                    'You need to <a class="js-login" '
                    'href="%(login_link)s">login</a> to access this page.',
                    msg_args
                )
                ctx["login_message"] = login_msg

            return HttpResponseForbidden(
                render_to_string('errors/403.html', context=ctx,
                                 request=request))
        elif (exception.__class__.__name__ in
                ('OperationalError', 'ProgrammingError', 'DatabaseError')):
            # HACKISH: Since exceptions thrown by different databases do not
            # share the same class heirarchy (DBAPI2 sucks) we have to check
            # the class name instead. Since python uses duck typing I will call
            # this poking-the-duck-until-it-quacks-like-a-duck-test
            return handle_exception(request, exception, 'errors/db.html')
        else:
            return handle_exception(request, exception, 'errors/500.html')
