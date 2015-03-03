#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings

from pootle.__version__ import sver
from pootle_language.models import Language
from pootle_project.models import Project
from staticpages.models import LegalPage

from .util import jsonify


def _agreement_context(request):
    """Returns whether the agreement box should be displayed or not."""
    request_path = request.META['PATH_INFO']
    nocheck = filter(lambda x: request_path.startswith(x),
                     settings.LEGALPAGE_NOCHECK_PREFIXES)

    if (request.user.is_authenticated() and not nocheck and
        LegalPage.objects.pending_user_agreement(request.user).exists()):
        return True

    return False


def _get_social_auth_providers(request):
    if 'allauth.socialaccount' not in settings.INSTALLED_APPS:
        return []

    from allauth.socialaccount import providers
    return [{'name': provider.name, 'url': provider.get_login_url(request)}
            for provider in providers.registry.get_list()]


def pootle_context(request):
    """Exposes settings to templates."""
    #FIXME: maybe we should expose relevant settings only?
    return {
        'settings': {
            'TITLE': settings.TITLE,
            'POOTLE_INSTANCE_ID': settings.POOTLE_INSTANCE_ID,
            'CAN_CONTACT': settings.CAN_CONTACT and settings.CONTACT_EMAIL,
            'CAN_REGISTER': settings.CAN_REGISTER,
            'SCRIPT_NAME': settings.SCRIPT_NAME,
            'POOTLE_VERSION': sver,
            'CACHE_TIMEOUT': settings.CACHE_MIDDLEWARE_SECONDS,
            'POOTLE_CACHE_TIMEOUT': settings.POOTLE_CACHE_TIMEOUT,
            'DEBUG': settings.DEBUG,
        },
        'custom': settings.CUSTOM_TEMPLATE_CONTEXT,
        'ALL_LANGUAGES': Language.live.cached_dict(),
        'ALL_PROJECTS': Project.objects.cached_dict(request.user),
        'SOCIAL_AUTH_PROVIDERS': jsonify(_get_social_auth_providers(request)),
        'display_agreement': _agreement_context(request),
    }
