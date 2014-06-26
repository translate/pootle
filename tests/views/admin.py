#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import pytest

from django.core.urlresolvers import reverse_lazy


ADMIN_URL = reverse_lazy('pootle-admin')


@pytest.mark.django_db
def test_admin_not_logged_in(client):
    """Checks logged-out users cannot access the admin site."""
    response = client.get(ADMIN_URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_regular_user(client, default):
    """Checks regular users cannot access the admin site."""
    client.login(username=default.username, password='')
    response = client.get(ADMIN_URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_access(admin_client):
    """Tests that admin users can access the admin site."""
    response = admin_client.get(ADMIN_URL)
    assert response.status_code == 200
