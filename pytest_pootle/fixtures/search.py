# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest


UNITS_TEXT_SEARCH_TESTS = OrderedDict()
UNITS_TEXT_SEARCH_TESTS["case:Translated (source)"] = {
    "text": "Translated",
    "sfields": ["source"]}
UNITS_TEXT_SEARCH_TESTS["case:Translated (source/target)"] = {
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
UNITS_TEXT_SEARCH_TESTS["case:Translated (source_f/target_f)"] = {
    "text": "Translated",
    "sfields": ["source_f", "target_f"]}
UNITS_TEXT_SEARCH_TESTS["Suggestion for Translated (target_f)"] = {
    "text": "suggestion for translated",
    "sfields": ["target_f"]}
UNITS_TEXT_SEARCH_TESTS["suggestion for TRANSLATED (target_f)"] = {
    "text": "suggestion for TRANSLATED",
    "sfields": ["target_f"]}
UNITS_TEXT_SEARCH_TESTS["suggestion for translated (source_f)"] = {
    "text": "suggestion for translated",
    "sfields": ["source_f"],
    "empty": True}
UNITS_TEXT_SEARCH_TESTS["suggestion for translated (source/target)"] = {
    "text": "suggestion for translated",
    "sfields": ["target", "source"]}
UNITS_TEXT_SEARCH_TESTS["exact: suggestion for translated (target)"] = {
    "text": "Suggestion for Translated",
    "sfields": ["target"]}
UNITS_TEXT_SEARCH_TESTS["exact: suggestion for translated (source/target)"] = {
    "text": "Suggestion for Translated",
    "sfields": ["target", "source"]}
UNITS_TEXT_SEARCH_TESTS["suggestion translated for (target)"] = {
    "text": "suggestion translated for",
    "sfields": ["target"]}
UNITS_TEXT_SEARCH_TESTS["exact: suggestion translated for (target)"] = {
    "text": "suggestion translated for",
    "sfields": ["target"],
    "empty": True}
UNITS_TEXT_SEARCH_TESTS["FOO (notes)"] = {
    "text": "FOO",
    "sfields": ["notes"],
    "empty": True}
UNITS_TEXT_SEARCH_TESTS["FOO BAR"] = {
    "sfields": ["target", "source"],
    "empty": True}
# hmm - not 100% if this should pass or fail
UNITS_TEXT_SEARCH_TESTS["suggestion for translated FOO (target)"] = {
    "text": "suggestion translated for FOO",
    "sfields": ["target"],
    "empty": True}

UNITS_CONTRIB_SEARCH_TESTS = [
    "suggestions",
    "FOO",
    "my_suggestions",
    "user_suggestions",
    "user_suggestions_accepted",
    "user_suggestions_rejected",
    "my_submissions",
    "user_submissions",
    "my_submissions_overwritten",
    "user_submissions_overwritten"]

UNITS_STATE_SEARCH_TESTS = [
    "all",
    "translated",
    "untranslated",
    "fuzzy",
    "incomplete",
    "FOO"]

UNITS_CHECKS_SEARCH_TESTS = [
    "checks:foo",
    "category:foo",
    "category:critical",
    "checks:endpunc",
    "checks:endpunc,printf",
    "checks:endpunc,foo"]


@pytest.fixture(params=UNITS_STATE_SEARCH_TESTS)
def units_state_searches(request):
    return request.param


@pytest.fixture(params=UNITS_CHECKS_SEARCH_TESTS)
def units_checks_searches(request):
    from pootle_checks.utils import get_category_id

    check_type, check_data = request.param.split(":")
    if check_type == "category":
        return check_type, get_category_id(check_data)
    return check_type, check_data.split(",")


@pytest.fixture(params=UNITS_CONTRIB_SEARCH_TESTS)
def units_contributor_searches(request):
    return request.param


@pytest.fixture(params=UNITS_TEXT_SEARCH_TESTS.keys())
def units_text_searches(request):
    text = request.param
    if text.startswith("case:"):
        text = text[6:]
        case = True
    else:
        case = False
    if text.startswith("exact:"):
        text = text[6:]
        exact = True
    else:
        exact = False
    test = UNITS_TEXT_SEARCH_TESTS[request.param]
    test["text"] = test.get("text", text)
    test["empty"] = test.get("empty", False)
    test["case"] = case
    test["exact"] = exact
    return test
