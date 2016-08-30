# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.primitives import PrefixedDict


def test_prefix_dict_no_prefix():
    mydict = dict(
        foo="apples",
        bar="oranges",
        baz="bananas")

    no_prefix = PrefixedDict(mydict, prefix="")

    for k, v in mydict.items():
        assert no_prefix[k] == v

    no_prefix["foo"] = "pears"
    no_prefix["other"] = "plums"

    assert mydict["foo"] == "pears"
    assert mydict["other"] == "plums"

    assert no_prefix.get("foo") == "pears"
    assert no_prefix.get("DOES NOT EXIST") is None
    assert no_prefix.get("DOES NOT EXIST", "pears") == "pears"


def test_prefix_dict_with_prefix():
    prefix = "some_prefix_"
    mydict = dict(
        foo="apples",
        bar="oranges",
        baz="bananas")
    with_prefix = PrefixedDict(mydict, prefix=prefix)

    with pytest.raises(KeyError):
        with_prefix["foo"]

    mydict = dict(
        some_prefix_foo="apples",
        some_prefix_bar="oranges",
        some_prefix_baz="bananas")
    with_prefix = PrefixedDict(mydict, prefix=prefix)

    for k, v in mydict.items():
        assert with_prefix[k[len(prefix):]] == v

    with_prefix["foo"] = "pears"
    with_prefix["other"] = "plums"

    assert mydict["%sfoo" % prefix] == "pears"
    assert mydict["%sother" % prefix] == "plums"

    assert with_prefix.get("foo") == "pears"
    assert with_prefix.get("DOES NOT EXIST") is None
    assert with_prefix.get("DOES NOT EXIST", "pears") == "pears"
