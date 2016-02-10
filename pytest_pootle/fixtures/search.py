# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from collections import OrderedDict


UNITS_TEXT_SEARCH_TESTS = OrderedDict()
UNITS_TEXT_SEARCH_TESTS["exact:Translated (source)"] = {
    "text": "Translated",
    "sfields": ["source"]}
UNITS_TEXT_SEARCH_TESTS["exact:Translated (source/target)"] = {
    "text": "Translated",
    "sfields": ["source", "target"]}
UNITS_TEXT_SEARCH_TESTS["Suggestion for Translated (target)"] = {
    "text": "suggestion for translated",
    "sfields": ["target"]}
UNITS_TEXT_SEARCH_TESTS["suggestion for TRANSLATED (target)"] = {
    "text": "suggestion for TRANSLATED",
    "sfields": ["target"]}
UNITS_TEXT_SEARCH_TESTS["suggestion for translated (source)"] = {
    "text": "suggestion for translated",
    "sfields": ["source"],
    "empty": True}
UNITS_TEXT_SEARCH_TESTS["suggestion for translated (source/target)"] = {
    "text": "suggestion for translated",
    "sfields": ["target", "source"]}
UNITS_TEXT_SEARCH_TESTS["exact: suggestion for translated (target)"] = {
    "text": "suggestion for translated",
    "sfields": ["target"]}
UNITS_TEXT_SEARCH_TESTS["exact: suggestion for translated (source/target)"] = {
    "text": "suggestion for translated",
    "sfields": ["target", "source"]}
UNITS_TEXT_SEARCH_TESTS["suggestion translated for (target)"] = {
    "text": "suggestion translated for",
    "sfields": ["target"]}
UNITS_TEXT_SEARCH_TESTS["exact: suggestion translated for (target)"] = {
    "text": "suggestion translated for",
    "sfields": ["target"],
    "empty": True}
UNITS_TEXT_SEARCH_TESTS["FOO BAR"] = {
    "sfields": ["target", "source"],
    "empty": True}
# hmm - not 100% if this should pass or fail
UNITS_TEXT_SEARCH_TESTS["suggestion for translated FOO (target)"] = {
    "text": "suggestion translated for FOO",
    "sfields": ["target"],
    "empty": True}


@pytest.fixture(params=UNITS_TEXT_SEARCH_TESTS.keys())
def units_text_searches(request):
    text = request.param
    if text.startswith("exact:"):
        text = text[6:]
        exact = True
    else:
        exact = False
    test = UNITS_TEXT_SEARCH_TESTS[request.param]
    test["text"] = test.get("text", text)
    test["empty"] = test.get("empty", False)
    test["exact"] = exact
    return test
