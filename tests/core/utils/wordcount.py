#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.storage.statsdb import wordcount as ttk_wordcount

from pootle.core.utils.wordcount import wordcount as ptl_wordcount
from pootle_pytest.fixtures.core.utils.wordcount import WORDCOUNT_TESTS


def test_param_wordcount(wordcount_names):
    this_test = WORDCOUNT_TESTS[wordcount_names]
    assert ttk_wordcount(this_test["string"]) == this_test["ttk"]
    assert ptl_wordcount(this_test["string"]) == this_test["pootle"]
