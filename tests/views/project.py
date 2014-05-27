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

from pootle_language.models import Language
from pootle_project.models import Project

from ..utils import formset_dict


PROJECTS_ADMIN_URL = reverse_lazy('pootle-admin-projects')


@pytest.mark.xfail
def test_add_project(admin_client, english, tutorial):
    """Tests that we can add a project successfully."""
    new_project_code = 'test-project'
    new_project_name = 'Test Project'
    add_dict = {
        'code': new_project_code,
        'localfiletype': 'xlf',
        'fullname': new_project_name,
        'checkstyle': 'standard',
        'source_language': english.id,
        'treestyle': 'gnu',
    }

    response = admin_client.post(PROJECTS_ADMIN_URL, formset_dict([add_dict]))

    project_admin_url = reverse('pootle-project-admin-languages',
                                args=[new_project_code])
    project_admin_link = ''.join([
        '<a href="', project_admin_url, '">', new_project_code, '</a>'
    ])
    assert project_admin_link in response.content

    # Check for the actual model
    test_project = Project.objects.get(code=new_project_code)

    assert bool(test_project)
    assert test_project.fullname == add_dict['fullname']
    assert test_project.checkstyle == add_dict['checkstyle']
    assert test_project.localfiletype == add_dict['localfiletype']
    assert test_project.treestyle == add_dict['treestyle']


def test_project_list(admin_client, tutorial):
    """Tests that the admin project list contains the DB projects."""
    response = admin_client.get(PROJECTS_ADMIN_URL)

    project_admin_url = reverse('pootle-project-admin-languages',
                                args=[tutorial.code])
    project_admin_link = ''.join([
        '<a href="', project_admin_url, '">tutorial</a>'
    ])

    assert project_admin_link in response.content


@pytest.mark.xfail
@pytest.mark.django_db
def test_add_language(admin_client, fish, tutorial):
    """Tests a new language can be added to a project."""
    project_admin_url = reverse('pootle-project-admin-languages',
                                args=[tutorial.code])

    add_dict = {
        'language': fish.id,
        'project': tutorial.id,
    }
    response = admin_client.post(project_admin_url, formset_dict([add_dict]))
    tp_admin_permissions_url = reverse('pootle-tp-admin-permissions',
                                       args=[fish.code, tutorial.code])
    # If the link to the TP admin exists, the language was added
    # successfully
    assert tp_admin_permissions_url in response.content

    language_url = reverse('pootle-language-overview', args=[fish.code])
    response = admin_client.get(language_url)

    tp_url = reverse('pootle-tp-overview',
                     args=[fish.code, tutorial.code, '', ''])
    # The language page should contain a link to the new TP
    assert ''.join(['<a href="', tp_url, '">']) in response.content
