# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from __future__ import absolute_import

import pytest

from django.urls import reverse

from pootle_store.models import Unit


@pytest.mark.django_db
def test_contact_report_form_view(client, request_users, rf):
    unit = Unit.objects.last()
    url = '%s?report=%s' % (reverse('pootle-contact-report-error'), unit.pk)
    user = request_users["user"]
    if user.username != "nobody":
        client.login(username=user.username, password=user.password)
    response = client.get(url)

    assert response.status_code == 200
    assert 'contact_form_title' in response.context
    url = reverse('pootle-contact-report-error')
    assert response.context['contact_form_url'] == url

    assert not hasattr(response.context["form"], "unit")
    assert not hasattr(response.context["view"], "unit")


@pytest.mark.django_db
def test_contact_report_form_view_no_unit(client, admin, rf):
    url = reverse('pootle-contact-report-error')
    client.login(username=admin.username, password=admin.password)
    response = client.get(url)

    assert response.status_code == 200
    assert not hasattr(response.context["view"], "unit")
    assert 'context' not in response.context['view'].get_initial()


@pytest.mark.django_db
def test_contact_report_form_view_blank_unit(client, admin, rf):
    url = '%s?report=' % reverse('pootle-contact-report-error')
    client.login(username=admin.username, password=admin.password)
    response = client.get(url)

    assert response.status_code == 200
    assert not hasattr(response.context["view"], "unit")


@pytest.mark.django_db
def test_contact_report_form_view_no_numeric_unit(client, admin, rf):
    url = '%s?report=STRING' % reverse('pootle-contact-report-error')
    client.login(username=admin.username, password=admin.password)
    response = client.get(url)

    assert response.status_code == 200
    assert not hasattr(response.context["view"], "unit")


@pytest.mark.django_db
def test_contact_report_form_view_unexisting_unit(client, admin, rf):
    unit_pk = 99999999
    Unit.objects.filter(id=unit_pk).delete()  # Ensure unit doesn't exist.
    url = '%s?report=%s' % (reverse('pootle-contact-report-error'), unit_pk)
    client.login(username=admin.username, password=admin.password)
    response = client.get(url)

    assert response.status_code == 200
    assert not hasattr(response.context["view"], "unit")
