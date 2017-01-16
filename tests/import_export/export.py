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
