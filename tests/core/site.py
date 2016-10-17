# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.contrib.sites.models import Site

from pootle.core.delegate import site


@pytest.mark.django_db
def test_site(settings):
    # default using Sites framework
    settings.POOTLE_CANONICAL_URL = ""
    pootle_site = site.get()
    assert (
        pootle_site.build_absolute_uri("/foo")
        == u'https://example.com/foo')
    assert not pootle_site.use_insecure_http
    settings.USE_INSECURE_HTTP = True
    assert pootle_site.use_insecure_http
    assert (
        pootle_site.build_absolute_uri("/foo")
        == u'http://example.com/foo')
    contrib_site = Site.objects.get_current()
    contrib_site.domain = "foo.com"
    contrib_site.save()
    assert (
        pootle_site.build_absolute_uri("/foo")
        == u'http://foo.com/foo')
    assert pootle_site.use_http_port == 80
    settings.USE_HTTP_PORT = 8008
    assert pootle_site.use_http_port == 8008
    assert (
        pootle_site.build_absolute_uri("/foo")
        == u'http://foo.com:8008/foo')


@pytest.mark.django_db
def test_site_canonical(settings):
    # default using POOTLE_CANONICAL_URL
    pootle_site = site.get()
    settings.POOTLE_CANONICAL_URL = "http://foo.com"
    assert not pootle_site.uses_sites
    assert not pootle_site.contrib_site
    assert pootle_site.use_insecure_http
    assert pootle_site.use_http_port == 80
    assert pootle_site.domain == "foo.com"
    assert (
        pootle_site.build_absolute_uri("/foo")
        == u'http://foo.com/foo')

    settings.POOTLE_CANONICAL_URL = "http://foo.com/bar"
    pootle_site = site.get()
    assert not pootle_site.uses_sites
    assert not pootle_site.contrib_site
    assert pootle_site.use_insecure_http
    assert pootle_site.use_http_port == 80
    assert pootle_site.domain == "foo.com"
    assert (
        pootle_site.build_absolute_uri("/foo")
        == u'http://foo.com/bar/foo')

    settings.POOTLE_CANONICAL_URL = "https://foo.com/bar"
    pootle_site = site.get()
    assert not pootle_site.uses_sites
    assert not pootle_site.contrib_site
    assert not pootle_site.use_insecure_http
    assert pootle_site.use_http_port == 80
    assert pootle_site.domain == "foo.com"
    assert (
        pootle_site.build_absolute_uri("/foo")
        == u'https://foo.com/bar/foo')

    settings.POOTLE_CANONICAL_URL = "https://foo.com:8008/bar"
    pootle_site = site.get()
    assert not pootle_site.uses_sites
    assert not pootle_site.contrib_site
    assert not pootle_site.use_insecure_http
    assert pootle_site.use_http_port == 8008
    assert pootle_site.domain == "foo.com"
    assert (
        pootle_site.build_absolute_uri("/foo")
        == u'https://foo.com:8008/bar/foo')
