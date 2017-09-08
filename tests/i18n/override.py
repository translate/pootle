# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.conf import settings
from django.utils.translation import LANGUAGE_SESSION_KEY

from pootle.i18n.override import (get_lang_from_cookie,
                                  get_lang_from_http_header,
                                  get_language_from_request,
                                  get_lang_from_session, supported_langs)


SUPPORTED_LANGUAGES = {
    'es-ar': 'es-ar',
    'fr': 'fr',
    'gl': 'gl',
}


@pytest.mark.django_db
def test_get_lang_from_session(rf, client):
    # Test no session.
    request = rf.get("")
    assert not hasattr(request, 'session')  # Check no session before test.
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) is None

    # Test session with no language.
    response = client.get("")
    request = response.wsgi_request
    assert LANGUAGE_SESSION_KEY not in request.session
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) is None

    # Test session with supported language.
    response = client.get("")
    request = response.wsgi_request
    request.session[LANGUAGE_SESSION_KEY] = 'gl'
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) == 'gl'

    # Test session with supported language.
    response = client.get("")
    request = response.wsgi_request
    request.session[LANGUAGE_SESSION_KEY] = 'es-AR'
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) == 'es-ar'

    # Test cookie with longer underscore language code for a supported
    # language.
    response = client.get("")
    request = response.wsgi_request
    request.session[LANGUAGE_SESSION_KEY] = 'gl_ES'
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) == 'gl'

    # Test cookie with longer hyphen language code for a supported language.
    response = client.get("")
    request = response.wsgi_request
    request.session[LANGUAGE_SESSION_KEY] = 'fr-FR'
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) == 'fr'

    # Test header with shorter language code for a supported language.
    response = client.get("")
    request = response.wsgi_request
    request.session[LANGUAGE_SESSION_KEY] = 'es'
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) is None

    # Test header with unsupported language.
    response = client.get("")
    request = response.wsgi_request
    request.session[LANGUAGE_SESSION_KEY] = 'FAIL'
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) is None

    # Test header with unsupported longer underscore language.
    response = client.get("")
    request = response.wsgi_request
    request.session[LANGUAGE_SESSION_KEY] = 'the_FAIL'
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) is None

    # Test header with unsupported longer hyphen language.
    response = client.get("")
    request = response.wsgi_request
    request.session[LANGUAGE_SESSION_KEY] = 'the-FAIL'
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) is None


def test_get_lang_from_cookie(rf):
    request = rf.get("")

    # Test no cookie.
    assert settings.LANGUAGE_COOKIE_NAME not in request.COOKIES
    assert get_lang_from_cookie(request, SUPPORTED_LANGUAGES) is None

    # Test cookie with supported language.
    request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = 'gl'
    assert get_lang_from_cookie(request, SUPPORTED_LANGUAGES) == 'gl'

    # Test cookie with longer supported language.
    request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = 'es-AR'
    assert get_lang_from_cookie(request, SUPPORTED_LANGUAGES) == 'es-ar'

    # Test cookie with longer underscore language code for a supported
    # language.
    request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = 'gl_ES'
    assert get_lang_from_cookie(request, SUPPORTED_LANGUAGES) == 'gl'

    # Test cookie with longer hyphen language code for a supported language.
    request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = 'fr-FR'
    assert get_lang_from_cookie(request, SUPPORTED_LANGUAGES) == 'fr'

    # Test cookie with shorter language code for a supported language.
    request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = 'es'
    assert get_lang_from_cookie(request, SUPPORTED_LANGUAGES) is None

    # Test cookie with unsupported language.
    request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = 'FAIL'
    assert get_lang_from_cookie(request, SUPPORTED_LANGUAGES) is None

    # Test cookie with unsupported longer underscore language.
    request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = 'the_FAIL'
    assert get_lang_from_cookie(request, SUPPORTED_LANGUAGES) is None

    # Test cookie with unsupported longer hyphen language.
    request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = 'the-FAIL'
    assert get_lang_from_cookie(request, SUPPORTED_LANGUAGES) is None


def test_get_lang_from_http_header(rf):
    # Test no header.
    request = rf.get("")
    assert 'HTTP_ACCEPT_LANGUAGE' not in request.META
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) is None

    # Test empty header.
    request = rf.get("", HTTP_ACCEPT_LANGUAGE='')
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) is None

    # Test header with wildcard.
    request = rf.get("", HTTP_ACCEPT_LANGUAGE='*')
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) is None

    # Test header with supported language.
    request = rf.get("", HTTP_ACCEPT_LANGUAGE='gl')
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) == 'gl'

    # Test cookie with longer supported language.
    request = rf.get("", HTTP_ACCEPT_LANGUAGE='es-AR')
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) == 'es-ar'

    # Test header with longer underscore language code for a supported
    # language.
    request = rf.get("", HTTP_ACCEPT_LANGUAGE='gl_ES')
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) is None

    # Test header with longer hyphen language code for a supported language.
    request = rf.get("", HTTP_ACCEPT_LANGUAGE='fr-FR')
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) == 'fr'

    # Test header with shorter language code for a supported language.
    request = rf.get("", HTTP_ACCEPT_LANGUAGE='es')
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) is None

    # Test header with unsupported language.
    request = rf.get("", HTTP_ACCEPT_LANGUAGE='FAIL')
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) is None

    # Test header with unsupported longer underscore language.
    request = rf.get("", HTTP_ACCEPT_LANGUAGE='the_FAIL')
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) is None

    # Test header with unsupported longer hyphen language.
    request = rf.get("", HTTP_ACCEPT_LANGUAGE='the-FAIL')
    assert get_lang_from_http_header(request, SUPPORTED_LANGUAGES) is None


def test_get_language_from_request(rf):
    settings_lang = settings.LANGUAGE_CODE
    supported = dict(supported_langs())  # Get Django supported languages.
    request = rf.get("")

    # Ensure the response doesn't come from any of the `lang_getter` functions.
    assert not hasattr(request, 'session')
    assert settings.LANGUAGE_COOKIE_NAME not in request.COOKIES
    assert 'HTTP_ACCEPT_LANGUAGE' not in request.META

    # Test default server language fallback.
    settings.LANGUAGE_CODE = 'it'
    assert settings.LANGUAGE_CODE in supported
    assert get_language_from_request(request) == settings.LANGUAGE_CODE

    # Test ultimate fallback.
    settings.LANGUAGE_CODE = 'FAIL-BABY-FAIL'
    assert settings.LANGUAGE_CODE not in supported
    assert get_language_from_request(request) == 'en-us'

    settings.LANGUAGE_CODE = settings_lang
