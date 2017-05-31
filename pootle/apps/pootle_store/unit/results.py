# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from itertools import groupby

from django.urls import reverse

from pootle.core.url_helpers import split_pootle_path
from pootle.i18n.gettext import language_dir
from pootle_store.constants import FUZZY
from pootle_store.models import Unit
from pootle_store.templatetags.store_tags import (
    pluralize_source, pluralize_target)
from pootle_store.unit.proxy import UnitProxy


class UnitResult(UnitProxy):

    @property
    def filetype(self):
        return self.unit["store__filetype__name"]

    @property
    def nplurals(self):
        return self.unit[
            "store__translation_project__language__nplurals"] or 0

    @property
    def pootle_path(self):
        return self.unit["store__pootle_path"]

    @property
    def project_code(self):
        return self.unit["store__translation_project__project__code"]

    @property
    def project_style(self):
        return self.unit[
            "store__translation_project__project__checkstyle"]

    @property
    def source_dir(self):
        return language_dir(self.source_lang)

    @property
    def source_lang(self):
        return self.unit[
            "store__translation_project__project__source_language__code"]

    @property
    def target_dir(self):
        return language_dir(self.target_lang)

    @property
    def target_lang(self):
        return self.unit[
            "store__translation_project__language__code"]

    @property
    def translate_url(self):
        return (
            u'%s%s'
            % (reverse("pootle-tp-store-translate",
                       args=split_pootle_path(self.pootle_path)),
               '#unit=%s' % unicode(self.id)))


class StoreResults(object):

    def __init__(self, units):
        self.units = units

    @property
    def data(self):
        meta = None
        units_list = []

        for unit in iter(self.units):
            unit = UnitResult(unit)
            if meta is None:
                meta = {
                    'filetype': unit.filetype,
                    'source_lang': unit.source_lang,
                    'source_dir': unit.source_dir,
                    'target_lang': unit.target_lang,
                    'target_dir': unit.target_dir,
                    'project_code': unit.project_code,
                    'project_style': unit.project_style}
            units_list.append(
                {'id': unit.id,
                 'url': unit.translate_url,
                 'isfuzzy': unit.state == FUZZY,
                 'source': [source[1]
                            for source
                            in pluralize_source(unit)],
                 'target': [target[1]
                            for target
                            in pluralize_target(unit, unit.nplurals)]})
        return {
            'meta': meta,
            'units': units_list}


class GroupedResults(object):

    select_fields = [
        "id",
        "source_f",
        "target_f",
        "state",
        "store__filetype__name",
        "store__pootle_path",
        "store__translation_project__project__code",
        "store__translation_project__project__source_language__code",
        "store__translation_project__project__checkstyle",
        "store__translation_project__language__code",
        "store__translation_project__language__nplurals"]

    def __init__(self, units):
        self.units = units

    @property
    def data(self):
        unit_groups = []
        units = {
            unit["id"]: unit
            for unit
            in Unit.objects.filter(
                pk__in=self.units).values(*self.select_fields)}
        units = [units[pk] for pk in self.units]
        units_by_path = groupby(
            units,
            lambda x: x["store__pootle_path"])
        for pootle_path, units in units_by_path:
            unit_groups.append({pootle_path: StoreResults(units).data})
        return unit_groups
