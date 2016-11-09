# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property

from pootle_misc.checks import get_qualitycheck_list


class ChecksDisplay(object):

    def __init__(self, context):
        self.context = context

    @property
    def check_schema(self):
        return get_qualitycheck_list(self.context)

    @cached_property
    def check_data(self):
        return self.context.data_tool.get_checks()

    @property
    def checks_by_category(self):
        _checks = []
        for check in self.check_schema:
            if check["code"] not in self.check_data:
                continue
            check["count"] = self.check_data[check["code"]]
            _checks.append(check)
        return _checks
