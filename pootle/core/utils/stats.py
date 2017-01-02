# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.i18n.gettext import ugettext_lazy as _


# Maximal number of top contributors which is loaded for each request
TOP_CONTRIBUTORS_CHUNK_SIZE = 10


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
    states.append(make_dict('fuzzy', _("Fuzzy")))
    states.append(make_dict('untranslated', _("Untranslated")))

    return states
