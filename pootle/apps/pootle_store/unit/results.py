#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from itertools import groupby

from django.core.urlresolvers import reverse

from pootle.core.site import pootle_site
from pootle.core.url_helpers import split_pootle_path
from pootle_store.models import FUZZY
from pootle_store.templatetags.store_tags import (
    pluralize_source, pluralize_target)
from pootle_store.unit.proxy import UnitProxy


class UnitResult(UnitProxy):

    @property
    def language(self):
        return pootle_site.get_language(self.unit["language_id"])

    @property
    def nplurals(self):
        return self.language["nplurals"] or 0

    @property
    def pootle_path(self):
        return self.unit["pootle_path"]

    @property
    def project(self):
        return pootle_site.get_project(self.unit["project_id"])

    @property
    def project_code(self):
        return self.project["code"]

    @property
    def project_style(self):
        return self.project["checkstyle"]

    @property
    def source_dir(self):
        return pootle_site.languages[self.source_lang]["direction"]

    @property
    def source_lang(self):
        return pootle_site.get_language(self.project["source_language"])["code"]

    @property
    def target_dir(self):
        return pootle_site.languages[self.target_lang]["direction"]

    @property
    def target_lang(self):
        return self.language["code"]

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
        "pootle_path",
        "project_id",
        "language_id"]

    def __init__(self, units_qs):
        self.units_qs = units_qs

    @property
    def data(self):
        unit_groups = []
        units_by_path = groupby(
            self.units_qs.values(*self.select_fields),
            lambda x: x["pootle_path"])
        for pootle_path, units in units_by_path:
            unit_groups.append({pootle_path: StoreResults(units).data})
        return unit_groups
