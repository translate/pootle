#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.http import Http404

from pootle.core.decorators import get_path_obj, get_resource
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project, ProjectResource
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject


@pytest.mark.django_db
def test_get_path_obj(rf, default, afrikaans_tutorial):
    """Ensure the correct path object is retrieved."""
    language_code = afrikaans_tutorial.language.code
    project_code = afrikaans_tutorial.project.code

    language_code_fake = 'faf'
    project_code_fake = 'fake-tutorial'

    request = rf.get('/')
    request.user = default

    # Fake decorated function
    func = get_path_obj(lambda x, y: (x, y))

    # Single project
    func(request, project_code=project_code)
    assert isinstance(request.ctx_obj, Project)

    # Missing project
    with pytest.raises(Http404):
        func(request, project_code=project_code_fake)

    # Single language
    func(request, language_code=language_code)
    assert isinstance(request.ctx_obj, Language)

    # Missing language
    with pytest.raises(Http404):
        func(request, language_code=language_code_fake)

    # Translation Project
    func(request, language_code=language_code, project_code=project_code)
    assert isinstance(request.ctx_obj, TranslationProject)

    # Missing Translation Project
    with pytest.raises(Http404):
        func(request, language_code=language_code_fake,
             project_code=project_code)


@pytest.mark.django_db
def test_get_path_obj_disabled(rf, default, admin, project_foo,
                               afrikaans_tutorial,
                               arabic_tutorial_obsolete,
                               tutorial_disabled):
    """Ensure the correct path object is retrieved when projects are
    disabled (#3451) or translation projects are obsolete (#3682).
    """
    language_code = afrikaans_tutorial.language.code
    language_code_obsolete = arabic_tutorial_obsolete.language.code
    project_code_obsolete = arabic_tutorial_obsolete.project.code
    project_code_disabled = tutorial_disabled.code

    # Regular users first
    request = rf.get('/')
    request.user = default

    func = get_path_obj(lambda x, y: (x, y))

    # Single project
    func(request, project_code=project_foo.code)
    assert isinstance(request.ctx_obj, Project)

    with pytest.raises(Http404):
        func(request, project_code=project_code_disabled)

    # Disabled project
    with pytest.raises(Http404):
        func(request, language_code=language_code,
             project_code=project_code_disabled)

    # Obsolete translation project
    with pytest.raises(Http404):
        func(request, language_code=language_code_obsolete,
             project_code=project_code_obsolete)

    # Now admin users, they should have access to disabled projects too
    request = rf.get('/')
    request.user = admin

    func = get_path_obj(lambda x, y: (x, y))

    # Single project
    func(request, project_code=project_foo.code)
    assert isinstance(request.ctx_obj, Project)

    func(request, project_code=project_code_disabled)
    assert isinstance(request.ctx_obj, Project)

    # Disabled projects are still inaccessible
    with pytest.raises(Http404):
        func(request, language_code=language_code,
             project_code=project_code_disabled)

    # Obsolete translation projects are still inaccessible
    with pytest.raises(Http404):
        func(request, language_code=language_code_obsolete,
             project_code=project_code_obsolete)


@pytest.mark.django_db
def test_get_resource_tp(rf, default, tutorial, afrikaans_tutorial):
    """Tests that the correct resources are set for the given TP contexts."""
    store_name = 'tutorial.po'
    subdir_name = 'subdir/'

    subdir_name_fake = 'fake_subdir/'
    store_name_fake = 'fake_store.po'

    request = rf.get('/')
    request.user = default

    # Fake decorated function
    func = get_resource(lambda x, y, s, t: (x, y, s, t))

    # TP, no resource
    func(request, afrikaans_tutorial, '', '')
    assert isinstance(request.resource_obj, TranslationProject)

    # TP, file resource
    func(request, afrikaans_tutorial, '', store_name)
    assert isinstance(request.resource_obj, Store)

    # TP, directory resource
    func(request, afrikaans_tutorial, subdir_name, '')
    assert isinstance(request.resource_obj, Directory)

    # TP, missing file/dir resource, redirects to parent resource
    response = func(request, afrikaans_tutorial, '', store_name_fake)
    assert response.status_code == 302
    assert afrikaans_tutorial.pootle_path in response.get('location')

    response = func(request, afrikaans_tutorial, subdir_name, store_name_fake)
    assert response.status_code == 302
    assert (''.join([afrikaans_tutorial.pootle_path, subdir_name]) in
            response.get('location'))

    response = func(request, afrikaans_tutorial, subdir_name_fake, '')
    assert response.status_code == 302
    assert afrikaans_tutorial.pootle_path in response.get('location')


@pytest.mark.django_db
def test_get_resource_project(rf, default, tutorial, afrikaans_tutorial,
                              arabic_tutorial_obsolete):
    """Tests that the correct resources are set for the given Project
    contexts.
    """
    store_name = 'tutorial.po'
    subdir_name = 'subdir/'

    request = rf.get('/')
    request.user = default

    # Fake decorated function
    func = get_resource(lambda x, y, s, t: (x, y, s, t))

    # Project, no resource
    func(request, tutorial, '', '')
    assert isinstance(request.resource_obj, Project)

    # Project, cross-language file resource
    func(request, tutorial, '', store_name)
    assert isinstance(request.resource_obj, ProjectResource)

    # Two languages had this file, but it was marked as obsolete for the Arabic
    # language!
    # Should only contain a single file resource
    assert len(request.resource_obj.resources) == 1
    assert isinstance(request.resource_obj.resources[0], Store)

    # Project, cross-language directory resource
    func(request, tutorial, subdir_name, '')
    assert isinstance(request.resource_obj, ProjectResource)

    # Two languages have this dir, but it was marked as obsolete for the Arabic
    # language!
    # Should only contain a single dir resource
    assert len(request.resource_obj.resources) == 1
    assert isinstance(request.resource_obj.resources[0], Directory)
