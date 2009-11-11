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

from django.utils import translation
from django.utils.translation import trans_real
from django.conf import settings

from pootle.i18n import gettext
from pootle.i18n import gettext_live

class LocaleMiddleware(object):
    """
    Load user specified locale from profile and inject it in
    session for django's locale middle ware to find.
    """

    def process_request(self, request):
        if request.user.is_authenticated() and 'django_language' not in request.session:
            language = request.user.get_profile().ui_lang
            if language is not None:
                request.session['django_language'] = language.code
            else:
                request.session['django_language'] = None
