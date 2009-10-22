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

# This code is based on a Django snippet by the user sgb at 
# http://www.djangosnippets.org/snippets/727/

import sys
import logging

from django.conf import settings
try:
    import cProfile
    from profiling import lsprofcalltree
except ImportError:
    pass

class ProfilerMiddleware(object):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not sys.version_info < (2,5) and settings.DEBUG and 'prof' in request.GET:
            self.profiler = cProfile.Profile()
            args = (request,) + callback_args
            return self.profiler.runcall(callback, *args, **callback_kwargs)

    def process_response(self, request, response):
        if not sys.version_info < (2,5) and settings.DEBUG and 'prof' in request.GET:
            logging.info("Profiling to the file %s", request.GET['prof'])
            cache_grind_data = lsprofcalltree.KCacheGrind(self.profiler)
            f = None
            try:
                f = open(request.GET['prof'], 'w')
                cache_grind_data.output(f)
            finally:
                if f is not None:
                    f.close()
        return response
