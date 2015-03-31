#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import sys
import traceback

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.http import (Http404, HttpResponse, HttpResponseForbidden,
                         HttpResponseServerError)
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _

try:
    from raven.contrib.django.models import sentry_exception_handler
except ImportError:
    sentry_exception_handler = None

from pootle.core.exceptions import Http400
from pootle_misc.baseurl import get_next
from pootle_misc.util import jsonify


class ErrorPagesMiddleware(object):
    """Friendlier error pages."""

    def _ajax_error(self, rcode, msg):
        error_body = {
            'msg': msg,
        }
        response = jsonify(error_body)
        return HttpResponse(response, status=rcode,
                            content_type="application/json")

    def process_exception(self, request, exception):
        msg = force_unicode(exception)
        if isinstance(exception, Http404):
            if request.is_ajax():
                return self._ajax_error(404, msg)
        elif isinstance(exception, Http400):
            if request.is_ajax():
                return self._ajax_error(400, msg)
        elif isinstance(exception, PermissionDenied):
            if request.is_ajax():
                return self._ajax_error(403, msg)

            templatevars = {
                'permission_error': msg,
            }

            if not request.user.is_authenticated():
                msg_args = {
                    'login_link': "%s%s" % (reverse('account_login'),
                                            get_next(request)),
                }
                login_msg = _('You need to <a href="%(login_link)s">login</a> '
                              'to access this page.', msg_args)
                templatevars["login_message"] = login_msg

            return HttpResponseForbidden(
                    render_to_string('errors/403.html', templatevars,
                                     RequestContext(request))
                )
        elif (exception.__class__.__name__ in
                ('OperationalError', 'ProgrammingError', 'DatabaseError')):
            # HACKISH: Since exceptions thrown by different databases do
            # not share the same class heirarchy (DBAPI2 sucks) we have to
            # check the class name instead. Since python uses duck typing
            # I will call this
            # poking-the-duck-until-it-quacks-like-a-duck-test

            if request.is_ajax():
                return self._ajax_error(500, msg)

            return HttpResponseServerError(
                    render_to_string('errors/db.html', {'exception': msg},
                                     RequestContext(request))
                )

        else:
            #FIXME: implement better 500
            tb = traceback.format_exc()
            print >> sys.stderr, tb

            if not settings.DEBUG:
                try:
                    templatevars = {
                        'exception': msg,
                    }
                    if hasattr(exception, 'filename'):
                        msg_args = {
                            'filename': exception.filename,
                            'errormsg': exception.strerror,
                        }
                        msg = _('Error accessing %(filename)s, Filesystem '
                                'sent error: %(errormsg)s', msg_args)
                        templatevars['fserror'] = msg

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

                    if request.is_ajax():
                        return self._ajax_error(500, msg)

                    return HttpResponseServerError(
                        render_to_string('errors/500.html', templatevars,
                                         RequestContext(request)))
                except:
                    # Let's not confuse things by throwing an exception here
                    pass
