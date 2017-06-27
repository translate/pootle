# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_store.views import get_alt_src_langs


def do_test_get_altsrclangs_nobody(nobody, language, unit, client):
    tp = unit.store.translation_project

    response = client.get(
        "/xhr/units/%s/edit/" % unit.id,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    request = response.wsgi_request

    # User has no altsrclangs and no HTTP_ACCEPT_LANGUAGE.
    nobody.alt_src_langs.clear()
    alt_src_langs = get_alt_src_langs(request, nobody, tp)
    assert alt_src_langs is None

    # User has altsrclangs and no HTTP_ACCEPT_LANGUAGE.
    nobody.alt_src_langs.clear()
    nobody.alt_src_langs.add(language)
    alt_src_langs = get_alt_src_langs(request, nobody, tp)
    assert alt_src_langs is None

    # HTTP_ACCEPT_LANGUAGE and no user's altsrclangs.
    nobody.alt_src_langs.clear()
    response = client.get(
        "/xhr/units/%s/edit/" % unit.id,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        HTTP_ACCEPT_LANGUAGE=language.code)
    request = response.wsgi_request
    alt_src_langs = get_alt_src_langs(request, nobody, tp)
    assert alt_src_langs is None

    # HTTP_ACCEPT_LANGUAGE and user has altsrclangs.
    nobody.alt_src_langs.add(language)
    alt_src_langs = get_alt_src_langs(request, nobody, tp)
    assert alt_src_langs is None


@pytest.mark.django_db
def test_get_altsrclangs(request_users, language0, get_edit_unit, client):
    user = request_users["user"]
    if user.username == "nobody":
        do_test_get_altsrclangs_nobody(user, language0, get_edit_unit, client)
        return

    client.login(
        username=user.username,
        password=request_users["password"])
    unit = get_edit_unit
    tp = unit.store.translation_project
    tp_lang = tp.language
    proj_source_lang = tp.project.source_language

    client_get_kwargs = {
        'path': "/xhr/units/%s/edit/" % unit.id,
        'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
    }
    request = client.get(**client_get_kwargs).wsgi_request

    # User has altsrclang different to TP or Project.
    user.alt_src_langs.clear()
    user.alt_src_langs.add(language0)
    alt_src_langs = get_alt_src_langs(request, user, tp)
    assert language0 in alt_src_langs

    # User altsrclang is TP language.
    user.alt_src_langs.clear()
    user.alt_src_langs.add(tp_lang)
    alt_src_langs = get_alt_src_langs(request, user, tp)
    assert alt_src_langs is None
    assert tp.project.translationproject_set.filter(language=tp_lang).exists()

    # User altsrclang is Project's source language.
    user.alt_src_langs.clear()
    user.alt_src_langs.add(proj_source_lang)
    prev_tp_lang = tp.language
    tp.language = proj_source_lang
    tp.save()
    alt_src_langs = get_alt_src_langs(request, user, tp)
    assert alt_src_langs is None
    assert tp.project.translationproject_set.filter(
        language=proj_source_lang).exists()
    tp.language = prev_tp_lang
    tp.save()

    # User has no altsrclangs and no HTTP_ACCEPT_LANGUAGE is provided.
    user.alt_src_langs.clear()
    alt_src_langs = get_alt_src_langs(request, user, tp)
    assert alt_src_langs is None

    # Test scenarios for HTTP_ACCEPT_LANGUAGE and no user's altsrclangs.
    user.alt_src_langs.clear()

    def set_accept_lang_and_get_altsrclangs(lang_code):
        client_get_kwargs['HTTP_ACCEPT_LANGUAGE'] = lang_code
        request = client.get(**client_get_kwargs).wsgi_request
        return get_alt_src_langs(request, user, tp)

    language0.code = "zz"
    language0.save()
    alt_src_langs = set_accept_lang_and_get_altsrclangs(language0.code)
    assert language0 in alt_src_langs

    alt_src_langs = set_accept_lang_and_get_altsrclangs('%s-COUNTRY' %
                                                        language0.code)
    assert language0 in alt_src_langs

    alt_src_langs = set_accept_lang_and_get_altsrclangs(tp_lang.code)
    assert alt_src_langs is None

    alt_src_langs = set_accept_lang_and_get_altsrclangs(proj_source_lang.code)
    assert alt_src_langs is None

    alt_src_langs = set_accept_lang_and_get_altsrclangs('*')
    assert alt_src_langs is None

    alt_src_langs = set_accept_lang_and_get_altsrclangs('templates')
    assert alt_src_langs is None

    alt_src_langs = set_accept_lang_and_get_altsrclangs('en')
    assert alt_src_langs is None

    alt_src_langs = set_accept_lang_and_get_altsrclangs('en_US')
    assert alt_src_langs is None

    alt_src_langs = set_accept_lang_and_get_altsrclangs('DOES_NOT_EXIST')
    assert alt_src_langs is None
