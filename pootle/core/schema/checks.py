# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re


class MySQLDefaultsChecker(object):
    required_settings = {
        'collation': r'utf8.*',
        'character_set': r'utf8.*',
    }

    def check(self, defaults):
        result = True
        for key, value in defaults.items():
            if key in self.required_settings:
                result &= bool(re.match(self.required_settings[key], value))

        return result

    def state(self, defaults):
        results = []
        for key, value in defaults.items():
            results.append({
                'field': key,
                'value': value,
                'pattern': self.required_settings[key],
                'status': bool(re.match(self.required_settings[key], value)),
            })

        return results
