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

from django.utils.translation import gettext as _


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


def get_translate_actions(path_obj):
    """Return a list of translation action links to be displayed for each ``path_obj``."""
    goal_url = ''
    goal_words = 0

    if path_obj.is_dir:
        # Putting the next import at the top of the file causes circular
        # import issues.
        from pootle_tagging.models import Goal

        goal = Goal.get_most_important_incomplete_for_path(path_obj)

        if goal is not None:
            goal_words = goal.get_incomplete_words_in_path(path_obj)
            goal_url = goal.get_translate_url_for_path(path_obj.pootle_path,
                                                       state='incomplete')

    return {
        'is_dir': path_obj.is_dir,
        'nextGoal': goal_words,
        'nextGoalUrl': goal_url,
        'translate_url': path_obj.get_translate_url(state='all'),
        'incomplete_url': path_obj.get_translate_url(state='incomplete'),
        'suggestions_url': path_obj.get_translate_url(state='suggestions'),
        'critical_url': path_obj.get_critical_url(),
    }


def stats_message_raw(version, total, translated, fuzzy):
    """Build a message of statistics used in VCS actions."""
    return "%s: %d of %d strings translated (%d need review)." % \
           (version, translated, total, fuzzy)
