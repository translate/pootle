# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest

from pootle.core.plugin.delegate import Provider
from pootle.core.plugin.results import GatheredDict, GatheredList


def test_gathered_dict():

    provider_test = Provider()

    with pytest.raises(TypeError):
        GatheredDict()

    members = (
        ("foo3", "bar1"),
        ("foo2", "bar2"),
        ("foo1", "bar3"))
    memberdict = OrderedDict(members)
    gd = GatheredDict(provider_test)
    [gd.add_result(None, dict((member, )))
     for member in members]
    assert gd.keys() == memberdict.keys()
    assert gd.values() == memberdict.values()
    assert gd.items() == memberdict.items()
    assert [x for x in gd] == memberdict.keys()
    assert all((k in gd) for k in memberdict.keys())


def test_gathered_dict_update():

    provider_test = Provider()
    members = (
        ("foo3", "bar1"),
        ("foo2", "bar2"),
        ("foo1", "bar3"))
    memberdict = OrderedDict(members)
    gd = GatheredDict(provider_test)
    [gd.add_result(None, dict((member, )))
     for member in members]
    # None results are ignored
    gd.add_result(None, None)
    newdict = dict()
    newdict.update(gd)
    assert all((k in newdict) for k in memberdict.keys())
    assert all((newdict[k] == v) for k, v in memberdict.items())
    assert len(newdict) == len(memberdict)


def test_gathered_list():

    provider_test = Provider()

    with pytest.raises(TypeError):
        GatheredList()

    provider_test = Provider()
    gl = GatheredList(provider_test)
    members = [
        [2, 3, 4],
        [3, 4, 5],
        [4, 4, 7],
        ["foo", "bar"],
        None]
    memberlist = []
    [memberlist.extend(member) for member in members if member]
    [gl.add_result(None, member)
     for member in members]
    assert list(gl) == memberlist
    assert [x for x in gl] == memberlist
    assert all((k in gl) for k in memberlist)
    newlist = []
    newlist.extend(gl)
    assert newlist == memberlist
