# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.i18n.gettext import language_dir
from pootle_store.templatetags.store_tags import pluralize_target

from .proxy import UnitProxy


class AltSrcUnitProxy(UnitProxy):
    @property
    def language_code(self):
        return self.unit["store__translation_project__language__code"]

    @property
    def language_direction(self):
        return language_dir(self.language_code)

    @property
    def language_name(self):
        return self.unit["store__translation_project__language__fullname"]

    @property
    def nplurals(self):
        return self.unit["store__translation_project__language__nplurals"] or 0

    @property
    def data(self):
        return dict(
            id=self.id,
            language_code=self.language_code,
            language_name=self.language_name,
            language_direction=self.language_direction,
            nplurals=self.nplurals,
            has_plurals=self.hasplural(),
            target=[target[1]
                    for target
                    in pluralize_target(self, self.nplurals)],
        )


class AltSrcUnits(object):
    fields = {
        "id",
        "source_f",
        "target_f",
        "store__translation_project__language__code",
        "store__translation_project__language__fullname",
        "store__translation_project__language__nplurals",
    }

    def __init__(self, qs):
        self.qs = qs

    @property
    def units(self):
        return [AltSrcUnitProxy(x) for x in self.qs.values(*self.fields)]
