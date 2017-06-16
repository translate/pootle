# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.utils import translation

from pootle.core.delegate import language_code
from pootle.core.language import LanguageCode


def test_language_code_util():
    assert language_code.get() == LanguageCode


def _server_lang_matches_request(ignore_dialect=True):
    """checks whether server lang matches request lang.

    if ignore dialect is set, dialects are ignored
    """
    server_code = LanguageCode(settings.LANGUAGE_CODE)
    request_code = LanguageCode(translation.get_language())
    return server_code.matches(request_code, ignore_dialect=ignore_dialect)


def test_language_server_request_match(settings):
    # default LANGUAGE_CODE = "en-us"
    with translation.override(settings.LANGUAGE_CODE):
        assert (
            _server_lang_matches_request()
            is True)
        assert (
            _server_lang_matches_request(ignore_dialect=False)
            is True)

    # check against en and dialects
    en_dialects = ["en-GB", "en-gb", "en@gb", "en_GB", "en-FOO"]
    with translation.override("en"):
        assert (
            _server_lang_matches_request()
            is True)
        assert (
            _server_lang_matches_request(ignore_dialect=False)
            is False)
    for lang_code in en_dialects:
        with translation.override(lang_code):
            assert (
                _server_lang_matches_request()
                is True)
            assert (
                _server_lang_matches_request(ignore_dialect=False)
                is False)
    # check against es and dialects
    es_dialects = ["es", "es-MX", "es-mx", "es@mx", "es_MX", "es-FOO"]
    for lang_code in es_dialects:
        with translation.override(lang_code):
            assert (
                _server_lang_matches_request()
                is False)
            assert (
                _server_lang_matches_request(ignore_dialect=False)
                is False)
