# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings

from pootle.core.markup import get_markup_filter_name
from pootle_project.models import Project
from staticpages.models import LegalPage


def _agreement_context(request):
    """Returns whether the agreement box should be displayed or not."""
    request_path = request.META['PATH_INFO']
    nocheck = filter(lambda x: request_path.startswith(x),
                     settings.POOTLE_LEGALPAGE_NOCHECK_PREFIXES)

    if (request.user.is_authenticated and not nocheck and
        LegalPage.objects.has_pending_agreement(request.user)):
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
    # FIXME: maybe we should expose relevant settings only?

    return {
        'settings': {
            'POOTLE_CUSTOM_LOGO': getattr(settings, "POOTLE_CUSTOM_LOGO", ""),
            'POOTLE_TITLE': settings.POOTLE_TITLE,
            'POOTLE_FAVICONS_PATH': settings.POOTLE_FAVICONS_PATH,
            'POOTLE_INSTANCE_ID': settings.POOTLE_INSTANCE_ID,
            'POOTLE_CONTACT_ENABLED': (settings.POOTLE_CONTACT_ENABLED and
                                       settings.POOTLE_CONTACT_EMAIL),
            'POOTLE_MARKUP_FILTER': get_markup_filter_name(),
            'POOTLE_SIGNUP_ENABLED': settings.POOTLE_SIGNUP_ENABLED,
            'SCRIPT_NAME': settings.SCRIPT_NAME,
            'POOTLE_CACHE_TIMEOUT': settings.POOTLE_CACHE_TIMEOUT,
            'DEBUG': settings.DEBUG,
        },
        'custom': settings.POOTLE_CUSTOM_TEMPLATE_CONTEXT,
        'ALL_PROJECTS': Project.objects.cached_dict(request.user),
        'SOCIAL_AUTH_PROVIDERS': _get_social_auth_providers(request),
        'display_agreement': _agreement_context(request),
    }
