# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.translation import to_locale


class LanguageCode(object):

    def __init__(self, code):
        self.code = code

    @property
    def normalized(self):
        return self.code.replace("_", "-").replace("@", "-").lower()

    @property
    def base_code(self):
        separator = self.normalized.rfind('-')
        return (
            self.code[:separator]
            if separator >= 0
            else self.code)

    def matches(self, other, ignore_dialect=True):
        return (
            (to_locale(self.code)
             == to_locale(other.code))
            or (ignore_dialect
                and (self.base_code
                     == (other.base_code))))
