#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from pootle_misc.baseurl import get_next

from .models import LegalPage


class LegalAgreementMiddleware(object):
    """Forces users to accept all legal documents defined for the site."""

    def process_request(self, request):
        request_path = request.META['PATH_INFO']
        nocheck = filter(lambda x: request_path.startswith(x),
                         settings.LEGALPAGE_NOCHECK_PREFIXES)

        if (request.user.is_authenticated() and not nocheck and
            LegalPage.objects.pending_user_agreement(request.user).exists()):
            return HttpResponseRedirect(
                u'%s%s' % (reverse('staticpages.legal-agreement'),
                           get_next(request)),
            )

        return None
