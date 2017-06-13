# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.urls import reverse

from import_export.utils import TPTMXExporter
from pootle.core.debug import memusage


@pytest.mark.pootle_memusage
@pytest.mark.django_db
def test_view_tp_export_garbage(client, tp0, language1, request_users):
    url = (
        "%s?path=/%s/%s/"
        % (reverse('pootle-export'),
           tp0.language.code,
           tp0.project.code))
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    client.get(url)
    for i in xrange(0, 2):
        with memusage() as usage:
            client.get(url)
        assert not usage["used"]
    url = (
        "%s?path=/%s/%s/"
        % (reverse('pootle-export'),
           language1.code,
           tp0.project.code))
    for i in xrange(0, 2):
        with memusage() as usage:
            client.get(url)
        assert not usage["used"]


@pytest.mark.django_db
def test_download_exported_tmx(client, tp0):
    args = [tp0.language.code, tp0.project.code]
    response = client.get(reverse('pootle-offline-tm-tp', args=args))
    assert response.status_code == 404
    exporter = TPTMXExporter(tp0)
    exporter.export()
    response = client.get(reverse('pootle-offline-tm-tp', args=args))
    assert response.status_code == 302
    assert response.url == exporter.get_url()


@pytest.mark.django_db
def test_view_context_with_exported_tmx(exported_tp_view_response):

    assert exported_tp_view_response.status_code == 200
    assert exported_tp_view_response.context['has_offline_tm']


@pytest.mark.django_db
def test_exported_tmx_url(client, tp0):
    args = [tp0.language.code, tp0.project.code]
    response = client.get(reverse('pootle-offline-tm-tp', args=args))
    assert response.status_code == 404
    exporter = TPTMXExporter(tp0)
    exporter.export()
    response = client.get(reverse('pootle-offline-tm-tp', args=args))
    assert response.status_code == 302
    exported_url = exporter.get_url()
    assert response.url == exported_url

    unit = tp0.stores.first().units.first()
    unit.target_f += ' CHANGED'
    unit.save()
    response = client.get(reverse('pootle-offline-tm-tp', args=args))
    assert response.status_code == 302
    assert response.url == exported_url


@pytest.mark.django_db
def test_wrong_language_exported_tmx_url(client):
    args = ('language_foo', 'project0')
    response = client.get(reverse('pootle-offline-tm-tp', args=args))
    assert response.status_code == 404
