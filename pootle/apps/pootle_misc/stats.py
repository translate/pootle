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

from django.core.urlresolvers import reverse
from django.utils.translation import ungettext


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
    goals_summary = []

    # Build URL for getting more summary information for the current path.
    url_path_summary_more = reverse('pootle-xhr-summary-more')

    if path_obj.is_dir:
        # Putting the next import at the top of the file causes circular
        # import issues.
        from pootle_tagging.models import Goal

        pootle_path = path_obj.pootle_path
        goal = Goal.get_most_important_incomplete_for_path(path_obj)

        if goal is not None:
            goal_words = goal.get_incomplete_words_in_path(path_obj)
            goal_url = goal.get_translate_url_for_path(pootle_path,
                                                       state='incomplete')
            if goal_words > 0:
                goals_summary.extend([
                    u'<br /><a class="continue-translation" href="%(url)s">' % {
                            'url': goal_url,
                        },
                    ungettext(u'<span class="caption">Next most important '
                              u'goal:</span> <span class="counter">%(num)d '
                              u'word left</span>',
                              u'<span class="caption">Next most important '
                              u'goal:</span> <span class="counter">%(num)d '
                              u'words left</span>',
                              goal_words,
                              {'num': goal_words, }),
                ])

    return {'is_dir': path_obj.is_dir,
            'goals_summary': u''.join(goals_summary),
            'summary_more_url': url_path_summary_more,
            'translate_url': path_obj.get_translate_url(state='all'),
            'incomplete_url': path_obj.get_translate_url(state='incomplete'),
            'suggestions_url': path_obj.get_translate_url(state='suggestions'),
            'critical_url': path_obj.get_critical_url(),
    }


def stats_message_raw(version, total, translated, fuzzy):
    """Build a message of statistics used in VCS actions."""
    return "%s: %d of %d strings translated (%d need review)." % \
           (version, translated, total, fuzzy)
