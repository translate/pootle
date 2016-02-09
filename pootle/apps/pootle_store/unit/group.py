# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from itertools import groupby

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from pootle.core.url_helpers import split_pootle_path
from pootle.i18n.gettext import language_dir
from pootle_store.util import FUZZY

from .proxy import UnitProxy


class GroupedUnit(UnitProxy):

    unit_mappings = (
        ("src_lang",
         "store__translation_project__project__source_language__code"),
        ("target_lang",
         "store__translation_project__language__code"),
        ("tp_lang_code",
         "store__translation_project__language__code"),
        ("project_code",
         "store__translation_project__project__code"),
        ("project_checkstyle",
         "store__translation_project__project__checkstyle"),
        ("pootle_path",
         "store__pootle_path"),
        ("nplurals",
         "store__translation_project__language__nplurals"))

    def __init__(self, unit):
        super(GroupedUnit, self).__init__(unit)
        for k, v in self.unit_mappings:
            self.unit[k] = self.unit[v]

    def get_translate_url(self):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)
        return u''.join(
            [reverse('pootle-tp-translate',
                     args=[lang, proj, dir, fn]),
             '#unit=%s' % unicode(self.id)])

    def isfuzzy(self):
        return self.state == FUZZY

    def pluralize_source(self):
        if not self.hasplural():
            return [(0, self.source, None)]

        count = len(self.source.strings)
        if count == 1:
            return [
                (0, self.source.strings[0],
                 "%s+%s" % (_('Singular'), _('Plural')))]

        if count == 2:
            return [
                (0, self.source.strings[0], _('Singular')),
                (1, self.source.strings[1], _('Plural'))]

        forms = []
        for i, source in enumerate(self.source.strings):
            forms.append((i, source, _('Plural Form %d', i)))
        return forms

    def pluralize_target(self):
        if not self.hasplural():
            return [(0, self.target, None)]

        forms = []
        if self.nplurals is None:
            for i, target in enumerate(self.target.strings):
                forms.append((i, target, _('Plural Form %d', i)))
        else:
            for i in range(self.nplurals):
                try:
                    target = self.target.strings[i]
                except IndexError:
                    target = ''
                forms.append((i, target, _('Plural Form %d', i)))

        return forms


class UnitGroups(object):

    def __init__(self, qs):
        self.qs = qs

    def group(self, path, units):
        meta = None
        units_list = []

        for unit in iter(units):
            unit = GroupedUnit(unit)
            if meta is None:
                meta = self._map_meta(unit)
            units_list.append(self._prepare_unit(unit))
        return {
            path: {
                'meta': meta,
                'units': units_list}}

    def group_units(self):
        unit_groups = []
        unit_fields = [
            "id", "state", "source_f", "target_f", "store__pootle_path"]
        unit_fields += dict(GroupedUnit.unit_mappings).values()
        unit_fields += self.qs.query.order_by
        units_by_path = groupby(
            self.qs.values(*unit_fields),
            lambda x: x['store__pootle_path'])
        for pootle_path, units in units_by_path:
            unit_groups.append(self.group(pootle_path, units))
        return unit_groups

    def _map_meta(self, unit):
        meta = {
            'source_lang': unit.src_lang,
            'target_lang': unit.target_lang,
            'project_code': unit.project_code,
            'project_style': unit.project_checkstyle}
        meta['source_dir'] = language_dir(meta["source_lang"])
        meta['target_dir'] = language_dir(meta["target_lang"])
        return meta

    def _prepare_unit(self, unit):
        """Constructs a dictionary with relevant `unit` data."""
        return {
            'id': unit.id,
            'url': unit.get_translate_url(),
            'isfuzzy': unit.isfuzzy(),
            'source': [source[1] for source in unit.pluralize_source()],
            'target': [target[1] for target in unit.pluralize_target()]}
