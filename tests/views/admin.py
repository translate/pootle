#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.urlresolvers import reverse_lazy


ADMIN_URL = reverse_lazy('pootle-admin')


@pytest.mark.django_db
def test_admin_not_logged_in(client):
    """Checks logged-out users cannot access the admin site."""
    response = client.get(ADMIN_URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_regular_user(client):
    """Checks regular users cannot access the admin site."""
    client.login(username="default", password='')
    response = client.get(ADMIN_URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_access(client):
    """Tests that admin users can access the admin site."""
    client.login(username="admin", password="admin")
    response = client.get(ADMIN_URL)
    assert response.status_code == 200
