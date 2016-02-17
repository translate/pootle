# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from pytest_pootle.search import calculate_search_results


@pytest.mark.django_db
def test_get_units(get_units_views):
    (user, search_params, url_params, response) = get_units_views
    result = json.loads(response.content)

    assert "unitGroups" in result
    assert isinstance(result["unitGroups"], list)
    if result["unitGroups"]:
        expected_uids, expected_units = calculate_search_results(
            search_params, user)

        if search_params.get("initial"):
            assert list(result["uIds"]) == list(expected_uids)
        else:
            assert "uIds" not in result

        for i, group in enumerate(expected_units):
            result_group = result["unitGroups"][i]
            for store, data in group.items():
                result_data = result_group[store]
                assert (
                    [u["url"] for u in result_data["units"]]
                    == [u["url"] for u in data["units"]])
