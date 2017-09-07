# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.utils.translation import LANGUAGE_SESSION_KEY

from pootle.i18n.override import get_lang_from_session


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
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) is None

    # Test cookie with longer underscore language code for a supported
    # language.
    response = client.get("")
    request = response.wsgi_request
    request.session[LANGUAGE_SESSION_KEY] = 'gl_ES'
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) is None

    # Test cookie with longer hyphen language code for a supported language.
    response = client.get("")
    request = response.wsgi_request
    request.session[LANGUAGE_SESSION_KEY] = 'fr-FR'
    assert get_lang_from_session(request, SUPPORTED_LANGUAGES) is None

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
