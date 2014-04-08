#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
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

from django.conf import settings

from pootle.__version__ import sver
from pootle_app.models.pootle_site import get_site_description, get_site_title
from pootle_language.models import Language
from pootle_project.models import Project
from staticpages.models import LegalPage


def _agreement_context(request):
    """Returns whether the agreement box should be displayed or not."""
    request_path = request.META['PATH_INFO']
    nocheck = filter(lambda x: request_path.startswith(x),
                     settings.LEGALPAGE_NOCHECK_PREFIXES)
    display_agreement = False

    if (request.user.is_authenticated() and not nocheck and
        LegalPage.objects.pending_user_agreement(request.user).exists()):
        display_agreement = True

    return {
        'display_agreement': display_agreement,
    }


def pootle_context(request):
    """Exposes settings to templates."""
    #FIXME: maybe we should expose relevant settings only?
    context = {
        'settings': {
            'TITLE': get_site_title(),
            'DESCRIPTION':  get_site_description(),
            'CAN_REGISTER': settings.CAN_REGISTER,
            'CAN_CONTACT': settings.CAN_CONTACT and settings.CONTACT_EMAIL,
            'SCRIPT_NAME': settings.SCRIPT_NAME,
            'POOTLE_VERSION': sver,
            'CACHE_TIMEOUT': settings.CACHE_MIDDLEWARE_SECONDS,
            'DEBUG': settings.DEBUG,
        },
        'custom': settings.CUSTOM_TEMPLATE_CONTEXT,
    }

    context.update({
        'ALL_LANGUAGES': Language.live.cached(),
        'ALL_PROJECTS': Project.objects.cached(),
    })

    context.update(_agreement_context(request))

    return context
