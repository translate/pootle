# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager

import pytest
from pytest_pootle.utils import suppress_getter

from pootle.core.delegate import context_data, tp_tool, wordcount


@contextmanager
def _no_wordcount():
    with suppress_getter(wordcount):
        yield


@pytest.fixture
def no_wordcount():
    return _no_wordcount


@contextmanager
def _no_context_data():
    with suppress_getter(context_data):
        yield


@pytest.fixture
def no_context_data():
    return _no_context_data


@contextmanager
def _no_tp_tool():
    with suppress_getter(tp_tool):
        yield


@pytest.fixture
def no_tp_tool():
    return _no_tp_tool
