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
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _, ungettext


def nice_percentage(count, total):
    """Return an integer percentage for count in respect to total.

    Avoid returning 0% or 100% for percentages closer to them since it might be
    misleading.
    """
    percentage = 100.0 * count / max(total, 1)

    # Let's try to be clever and make sure than anything above 0.0 and below
    # 0.5 will show as at least 1%, and anything above 99.5% and less than 100%
    # will show as 99%.
    if 99 < percentage < 100:
        return 99
    if 0 < percentage < 1:
        return 1
    return int(round(percentage))


def get_path_summary(path_obj, latest_action):
    """Return a list of sentences to be displayed for each ``path_obj``."""
    summary = []
    incomplete = []
    suggestions = []

    path_stats = path_obj.get_stats(False)

    if path_obj.is_dir:
        summary.append(
            ungettext("This folder has %(num)d word, %(percentage)d%% of "
                "which is translated.",
                "This folder has %(num)d words, %(percentage)d%% of "
                "which are translated.",
                path_stats['total'],
                {
                    'num': path_stats['total'],
                    'percentage': nice_percentage(path_stats['translated'],
                                  path_stats['total'])
                })
        )
    else:
        summary.append(
            ungettext("This file has %(num)d word, %(percentage)d%% of "
                "which is translated.",
                "This file has %(num)d words, %(percentage)d%% of "
                "which are translated.",
                path_stats['total'],
                {
                    'num': path_stats['total'],
                    'percentage': nice_percentage(path_stats['translated'],
                                  path_stats['total'])
                })
        )

    tp = path_obj.translation_project
    project = tp.project
    language = tp.language

    # Build URL for getting more summary information for the current path.
    url_args = [language.code, project.code, path_obj.path]
    url_path_summary_more = reverse('tp.path_summary_more', args=url_args)

    summary.append(u''.join([
        ' <a id="js-path-summary" data-target="js-path-summary-more" '
        'href="%s">' % url_path_summary_more,
        force_unicode(_(u'Expand details')),
        '</a>'
    ]))


    num_words = path_stats['total'] - path_stats['translated']
    if num_words > 0:
        incomplete.extend([
            u'<a class="path-incomplete" href="%(url)s">' % {
                    'url': path_obj.get_translate_url(state='incomplete')
                },
            ungettext(u'Continue translation (%(num)d word left)',
                      u'Continue translation (%(num)d words left)',
                      num_words,
                      {'num': num_words, }),
        ])

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
                incomplete.extend([
                    u'<br /><a class="path-incomplete" href="%(url)s">' % {
                            'url': goal_url,
                        },
                    ungettext(u'Next most important goal (%(num)d word left)',
                              u'Next most important goal (%(num)d words left)',
                              goal_words,
                              {'num': goal_words, }),
                ])
    else:
        incomplete.extend([
            u'<a class="path-incomplete" href="%(url)s">' % {
                    'url': path_obj.get_translate_url(state='all')
                },
            force_unicode(_('Translation is complete')),
        ])

    incomplete.append(u'</a>')


    if path_stats['suggestions'] > 0:
        suggestions.append(u'<a class="path-incomplete" href="%(url)s">' % {
            'url': path_obj.get_translate_url(state='suggestions')
        })
        suggestions.append(
            ungettext(u'Review suggestion (%(num)d left)',
                      u'Review suggestions (%(num)d left)',
                      path_stats['suggestions'],
                      {'num': path_stats['suggestions'], })
        )
        suggestions.append(u'</a>')

    return [u''.join(summary), latest_action, u''.join(incomplete),
            u''.join(suggestions)]


def stats_message_raw(version, total, translated, fuzzy):
    """Build a message of statistics used in VCS actions."""
    return "%s: %d of %d strings translated (%d need review)." % \
           (version, translated, total, fuzzy)
