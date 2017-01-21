# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.proxy import BaseProxy, AttributeProxy


def test_proxy_base_primitives():
    p = BaseProxy(3)
    assert issubclass(type(p), BaseProxy)
    assert p + 1 == 4
    p += 1
    assert type(p) == int
    assert p == 4
    assert BaseProxy([1, 2, 3]) + [4, 5] == [1, 2, 3, 4, 5]
    p = BaseProxy([1, 2, 3])
    p.extend(BaseProxy([4, 5]))
    assert p == [1, 2, 3, 4, 5]


def test_proxy_base_primitive_exceptions():

    # Proxying user-types should work perfectly well. But proxying builtin
    # objects, like ints, floats, lists, etc., has some limitation and
    # inconsistencies, imposed by the interprete

    p = BaseProxy(6)
    with pytest.raises(TypeError):
        p + p

    with pytest.raises(TypeError):
        assert BaseProxy([1, 2, 3]) + BaseProxy([4, 5])

    p = BaseProxy([1, 2, 3])
    with pytest.raises(TypeError):
        p + BaseProxy([6, 7])


def test_proxy_base():

    class Foo(object):

        bar = "BAR"

        @property
        def baz(self):
            return "BAZ"

        def dofoo(self):
            return "FOO"

    foo = Foo()
    wrapped = BaseProxy(foo)

    assert wrapped.bar == "BAR"
    assert wrapped.baz == "BAZ"
    assert wrapped.dofoo() == "FOO"
    assert str(wrapped) == str(foo)
    assert repr(wrapped) == repr(foo)
    wrapped.bar = "something else"
    assert foo.bar == "something else"
    wrapped.special_attr = "SPECIAL"
    assert foo.special_attr == "SPECIAL"
    delattr(wrapped, "special_attr")
    assert not hasattr(foo, "special_attr")
    assert wrapped
    assert not BaseProxy(0)


def test_proxy_attribute():

    class Foo(object):

        bar = "BAR"

        @property
        def baz(self):
            return "BAZ"

        def dofoo(self):
            return "FOO"

    foo = Foo()
    wrapped = AttributeProxy(foo)

    assert wrapped.bar == "BAR"
    assert wrapped.baz == "BAZ"
    assert wrapped.dofoo() == "FOO"

    wrapped.bar = "SOMETHING ELSE"
    assert foo.bar == "SOMETHING ELSE"

    wrapped.dofoo = "I USED TO BE A METHOD"
    assert foo.dofoo == "I USED TO BE A METHOD"

    with pytest.raises(AttributeError):
        wrapped.baz = "NO SETTING PROPERTIES"

    # extra attrs are only placed on the wrapper
    wrapped.special_attr = "SPECIAL"
    assert wrapped.special_attr == "SPECIAL"
    assert not hasattr(foo, "special_attr")

    delattr(wrapped, "special_attr")
    assert not hasattr(wrapped, "special_attr")

    delattr(wrapped, "bar")
    assert not hasattr(foo, "special_attr")
