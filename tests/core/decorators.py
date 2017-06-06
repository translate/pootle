# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.http import Http404

from pootle.core.cache import get_cache
from pootle.core.decorators import get_path_obj, persistent_property
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


@pytest.mark.django_db
def test_get_path_obj(rf, po_directory, default, tp0):
    """Ensure the correct path object is retrieved."""
    language_code = tp0.language.code
    project_code = tp0.project.code

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
def test_get_path_obj_disabled(rf, default, admin,
                               project0_nongnu,
                               tp0,
                               project_foo,
                               en_tutorial_obsolete,
                               tutorial_disabled):
    """Ensure the correct path object is retrieved when projects are
    disabled (#3451) or translation projects are obsolete (#3682).
    """
    language_code = tp0.language.code
    language_code_obsolete = en_tutorial_obsolete.language.code
    project_code_obsolete = en_tutorial_obsolete.project.code
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


def test_deco_persistent_property_no_cache_key():

    # no cache key set - uses instance caching
    class Foo(object):

        @persistent_property
        def bar(self):
            return "Baz"
    foo = Foo()
    assert foo.bar == "Baz"
    assert foo.__dict__ == dict(bar="Baz")

    # no cache key set and not always_cache - no caching
    class Foo(object):

        def _bar(self):
            return "Baz"
        bar = persistent_property(_bar, always_cache=False)
    foo = Foo()
    assert foo.bar == "Baz"
    assert foo.__dict__ == {}

    # no cache key set - uses instance caching with custom name
    class Foo(object):

        def _bar(self):
            return "Baz"
        bar = persistent_property(_bar, name="special_bar")
    foo = Foo()
    assert foo.bar == "Baz"
    assert foo.__dict__ == dict(special_bar="Baz")


def test_deco_persistent_property():

    # cache_key set - cached with it
    class Foo(object):
        cache_key = "foo-cache"

        @persistent_property
        def bar(self):
            """Get a bar man"""
            return "Baz"
    assert isinstance(Foo.bar, persistent_property)
    assert Foo.bar.__doc__ == "Get a bar man"
    foo = Foo()
    assert foo.bar == "Baz"
    assert get_cache("lru").get('pootle.core..foo-cache.bar') == "Baz"
    # cached version this time
    assert foo.bar == "Baz"

    # cache_key set with custom key attr - cached with it
    class Foo(object):
        special_key = "special-foo-cache"

        def _bar(self):
            return "Baz"
        bar = persistent_property(_bar, key_attr="special_key")
    foo = Foo()
    assert foo.bar == "Baz"
    assert get_cache("lru").get('pootle.core..special-foo-cache._bar') == "Baz"

    # cache_key set with custom key attr and name - cached with it
    class Foo(object):
        special_key = "special-foo-cache"

        def _bar(self):
            return "Baz"
        bar = persistent_property(
            _bar, name="bar", key_attr="special_key")
    foo = Foo()
    assert foo.bar == "Baz"
    assert get_cache("lru").get('pootle.core..special-foo-cache.bar') == "Baz"

    # cache_key set with custom namespace
    class Foo(object):
        ns = "pootle.foo"
        cache_key = "foo-cache"

        @persistent_property
        def bar(self):
            """Get a bar man"""
            return "Baz"

    foo = Foo()
    assert foo.bar == "Baz"
    assert get_cache("lru").get('pootle.foo..foo-cache.bar') == "Baz"
    # cached version this time
    assert foo.bar == "Baz"

    # cache_key set with custom namespace and sw_version
    class Foo(object):
        ns = "pootle.foo"
        cache_key = "foo-cache"
        sw_version = "0.2.3"

        @persistent_property
        def bar(self):
            """Get a bar man"""
            return "Baz"

    foo = Foo()
    assert foo.bar == "Baz"
    assert get_cache("lru").get('pootle.foo.0.2.3.foo-cache.bar') == "Baz"
    # cached version this time
    assert foo.bar == "Baz"
