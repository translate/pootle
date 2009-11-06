#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import traceback
import sys

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.db import DatabaseError
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from pootle_misc.baseurl import l

class ErrorPagesMiddleware(object):
    """
    Friendlier Error Pages
    """
    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            pass
        elif isinstance(exception, PermissionDenied):
            templatevars = { 'permission_error': exception.message }
            if not request.user.is_authenticated():
                login_msg = _('You need to <a href="%(login_link)s">login</a> to access this page.' % {'login_link': l("/accounts/login/") })
                templatevars["login_message"] = login_msg
            return render_to_response('403.html', templatevars,
                                      RequestContext(request))
        else:
            #FIXME: implement better 500
            traceback.print_exc(file=sys.stderr)
            
