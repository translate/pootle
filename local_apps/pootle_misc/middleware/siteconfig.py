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

import logging
import sys

from django.http import HttpResponse

from pootle_misc import siteconfig
from pootle_misc import dbinit
from pootle_misc import dbupdate

from pootle.__version__ import build as code_buildversion
from translate.__version__ import build as code_tt_buildversion

INSTALL_STATUS_CODE = 613
"""some unused http status code to mark the need to auto install"""

UPDATE_STATUS_CODE = 614
"""some unused http status code to mark the need to update database"""

DEFAULT_BUILDVERSION = 20000
"""Build version referring to Pootle version 2.0.
   we'll assume db represents version 2.0 if no build version is stored.
"""

DEFAULT_TT_BUILDVERSION = 12005
"""Build version referring to Translate Toolkit version 1.7.0.
   we'll assume db represents version 1.7.0 if no build version is stored.
"""

class SiteConfigMiddleware(object):
    """
    This middleware does two things, it reload djblet siteconfigs on
    every request to ensure they're uptodate. but also works as an
    early detection system for database errors.

    It might seem strange that the middleware does these two unrelated
    tasks, but since the only way to test the database is to run a
    query, it would be too wasteful to add another query per request
    when siteconfig already requires one.

    """
    def process_request(self, request):
        """load site config, return a dummy response if database seems uninitialized"""
        #FIXME: can't we find a more efficient method?
        try:
            response = HttpResponse()
            response.status_code = UPDATE_STATUS_CODE

            config = siteconfig.load_site_config()
            db_buildversion = int(config.get('BUILDVERSION', DEFAULT_BUILDVERSION))
            if db_buildversion < code_buildversion:
                response.db_buildversion = db_buildversion
                response.tt_buildversion = sys.maxint
            else:
                response.db_buildversion = sys.maxint

            db_tt_buildversion = int(config.get('TT_BUILDVERSION', DEFAULT_TT_BUILDVERSION))
            if db_tt_buildversion < code_tt_buildversion:
                """Toolkit build version changed. clear stale quality checks data"""
                logging.info("New Translate Toolkit version, flushing quality checks")
                dbupdate.flush_quality_checks()
                config.set('TT_BUILDVERSION', code_tt_buildversion)
                config.save()
                response.tt_buildversion = db_tt_buildversion

            if (response.db_buildversion, response.tt_buildversion) != (sys.maxint, sys.maxint):
                return response

        except Exception, e:
            #HACKISH: since exceptions thrown by different databases
            # do not share the same class heirarchy (DBAPI2 sucks) we
            # have to check the class name instead (since python uses
            # duck typing I will call this
            # poking-the-duck-until-it-quacks-like-a-duck-test

            if e.__class__.__name__ in ('OperationalError', 'ProgrammingError', 'DatabaseError'):
                # we can't build the database here cause caching
                # middleware won't allow progressive loading of
                # response so instead return an empty response marked
                # with special status code INSTALL_STATUS_CODE

                response = HttpResponse()
                response.status_code = INSTALL_STATUS_CODE
                response.exception = e
                return response


    def process_response(self, request, response):
        """ this should be the last response processor to run, detect
        dummy response with INSTALL_STATUS_CODE status code and start
        db install process"""

        if response.status_code == INSTALL_STATUS_CODE:
            return HttpResponse(dbinit.staggered_install(response.exception))
        elif response.status_code == UPDATE_STATUS_CODE:
            return HttpResponse(dbupdate.staggered_update(response.db_buildversion, response.tt_buildversion))
        else:
            return response
