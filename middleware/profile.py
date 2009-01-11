#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# This code is based on a Django snippet by the user sgb at 
# http://www.djangosnippets.org/snippets/727/

import sys
from django.conf import settings
try:
    import cProfile
    from Pootle.profiling import lsprofcalltree
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
            print "Profiling to the file %s" % request.GET['prof']
            cache_grind_data = lsprofcalltree.KCacheGrind(self.profiler)
            f = None
            try:
                f = open(request.GET['prof'], 'w')
                cache_grind_data.output(f)
            finally:
                if f is not None:
                    f.close()
        return response
