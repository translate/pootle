#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django.utils.translation import ugettext_lazy as _


def get_translation_states(path_obj):
    states = []

    def make_dict(state, title, filter_url=True):
        filter_name = filter_url and state or None
        return {
            'state': state,
            'title': title,
            'url': path_obj.get_translate_url(state=filter_name)
        }

    states.append(make_dict('total', _("Total"), False))
    states.append(make_dict('translated', _("Translated")))
    states.append(make_dict('fuzzy', _("Needs work")))
    states.append(make_dict('untranslated', _("Untranslated")))

    return states


def stats_message_raw(version, total, translated, fuzzy):
    """Build a message of statistics used in VCS actions."""
    return "%s: %d of %d strings translated (%d need review)." % \
           (version, translated, total, fuzzy)
