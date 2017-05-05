# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


class Result(object):

    def __init__(self):
        self.clear()

    def __getitem__(self, i):
        return self._results[i]

    def clear(self):
        self._results = []

    def add(self, *args):
        self._results.append(args)


@pytest.fixture
def dummy_filetypes_class():
    from pootle_format.utils import ProjectFiletypes

    class DummyProjectFiletypes(ProjectFiletypes):

        def set_tp_filetype(self, tp, filetype, from_filetype, matching):
            self.result.add(tp, filetype, from_filetype, matching)

    return DummyProjectFiletypes


@pytest.fixture
def dummy_project_filetypes(request, dummy_filetypes_class):
    from pootle.core.delegate import filetype_tool
    from pootle.core.plugin import getter
    from pootle_project.models import Project

    receivers = filetype_tool.receivers
    receiver_cache = filetype_tool.sender_receivers_cache.copy()
    filetype_tool.receivers = []
    filetype_tool.sender_receivers_cache.clear()

    result = Result()

    @getter(filetype_tool, sender=Project, weak=False)
    def filetype_tool_getter_(**kwargs_):
        dummy_filetypes_class.result = result
        return dummy_filetypes_class

    def _restore_filetypes():
        filetype_tool.receivers = receivers
        filetype_tool.sender_receivers_cache = receiver_cache

    request.addfinalizer(_restore_filetypes)
