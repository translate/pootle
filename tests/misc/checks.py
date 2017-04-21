# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_checks.constants import Category, CHECK_NAMES
from pootle_checks.utils import (
    get_category_code,
    get_category_name,
    get_qualitychecks,
    get_qualitycheck_list,
    get_qualitycheck_schema)


def test_get_qualitycheck_schema():
    d = {}
    checks = get_qualitychecks()
    for check, cat in checks.items():
        if cat not in d:
            d[cat] = {
                'code': cat,
                'name': get_category_code(cat),
                'title': get_category_name(cat),
                'checks': []
            }
        d[cat]['checks'].append({
            'code': check,
            'title': u"%s" % CHECK_NAMES.get(check, check),
            'url': ''
        })

    result = sorted([item for item in d.values()],
                    key=lambda x: x['code'],
                    reverse=True)

    assert result == get_qualitycheck_schema()


@pytest.mark.django_db
def test_get_qualitycheck_list(tp0):
    result = []
    checks = get_qualitychecks()
    for check, cat in checks.items():
        result.append({
            'code': check,
            'is_critical': cat == Category.CRITICAL,
            'title': u"%s" % CHECK_NAMES.get(check, check),
            'url': tp0.get_translate_url(check=check)
        })

    def alphabetical_critical_first(item):
        sort_prefix = 0 if item['is_critical'] else 1
        return "%d%s" % (sort_prefix, item['title'].lower())

    result = sorted(result, key=alphabetical_critical_first)

    assert result == get_qualitycheck_list(tp0)
