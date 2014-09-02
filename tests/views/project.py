#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

from django.core.urlresolvers import reverse, reverse_lazy


PROJECTS_ADMIN_URL = reverse_lazy('pootle-admin-projects')


def test_project_list(admin_client, tutorial):
    """Tests that the admin project list contains the DB projects."""
    response = admin_client.get(PROJECTS_ADMIN_URL)

    project_admin_url = reverse('pootle-project-admin-languages',
                                args=[tutorial.code])
    project_admin_link = ''.join([
        '<a href="', project_admin_url, '">tutorial</a>'
    ])

    assert project_admin_link in response.content
