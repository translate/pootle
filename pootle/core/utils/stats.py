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


def get_top_scorers_data(top_scorers, chunk_size):
    has_more_scorers = len(top_scorers) > chunk_size

    top_scorers_data = [
        dict(
            total_score=scorer['total_score'],
            public_total_score=scorer['public_total_score'],
            suggested=scorer['suggested'],
            translated=scorer['translated'],
            reviewed=scorer['reviewed'],
            email=scorer['user'].email_hash,
            display_name=scorer['user'].display_name,
            username=scorer['user'].username,
        ) for scorer in top_scorers[:chunk_size]
    ]

    return dict(
        items=top_scorers_data,
        has_more_items=has_more_scorers
    )
