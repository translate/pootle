# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.storage.statsdb import wordcount as ttk_wordcount

from pytest_pootle.fixtures.core.utils.wordcount import WORDCOUNT_TESTS


def test_param_wordcount(wordcount_names):
    this_test = WORDCOUNT_TESTS[wordcount_names]
    assert ttk_wordcount(this_test["string"]) == this_test["ttk"]
