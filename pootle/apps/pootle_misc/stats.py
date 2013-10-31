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


def add_percentages(quick_stats):
    """Add percentages onto the raw stats dictionary."""
    trans_percent = nice_percentage(quick_stats['translatedsourcewords'],
                                    quick_stats['totalsourcewords'])

    fuzzy_percent = nice_percentage(quick_stats['fuzzysourcewords'],
                                    quick_stats['totalsourcewords'])

    strtrans_percent = nice_percentage(quick_stats['translated'],
                                       quick_stats['total'])

    strfuzzy_percent = nice_percentage(quick_stats['fuzzy'],
                                       quick_stats['total'])

    quick_stats.update({
        'translatedpercentage': trans_percent,
        'fuzzypercentage':  fuzzy_percent,
        'untranslatedpercentage': 100 - trans_percent - fuzzy_percent,
        'strtranslatedpercentage': strtrans_percent,
        'strfuzzypercentage': strfuzzy_percent,
        'struntranslatedpercentage': 100 - strtrans_percent - strfuzzy_percent,
    })
    return quick_stats


def get_processed_stats(quick_stats):
    """Return a processed dictionary of raw stats."""
    return {
        'total': {
            'words': quick_stats['totalsourcewords'],
            'percentage': 100,
            'units': quick_stats['total'],
            },
        'translated': {
            'words': quick_stats['translatedsourcewords'],
            'percentage': quick_stats['translatedpercentage'],
            'units': quick_stats['translated'],
            },
        'fuzzy': {
            'words': quick_stats['fuzzysourcewords'],
            'percentage': quick_stats['fuzzypercentage'],
            'units': quick_stats['fuzzy'],
            },
        'untranslated': {
            'words': quick_stats['untranslatedsourcewords'],
            'percentage': quick_stats['untranslatedpercentage'],
            'units': quick_stats['untranslated'],
            },
        'errors': quick_stats['errors'],
        'suggestions': -1,
    }


def get_raw_stats(path_obj, include_suggestions=False):
    """Returns a dictionary of raw stats for `path_obj`.

    :param path_obj: A Directory/Store object.
    :param include_suggestions: Whether to include suggestion count in the
                                output or not.

    Example::

        {'translated': {'units': 0, 'percentage': 0, 'words': 0},
         'fuzzy': {'units': 0, 'percentage': 0, 'words': 0},
         'untranslated': {'units': 34, 'percentage': 100, 'words': 181},
         'total': {'units': 34, 'percentage': 100, 'words': 181}
         'suggestions': 4 }
    """
    stats = get_processed_stats(add_percentages(path_obj.getquickstats()))

    if include_suggestions:
        stats['suggestions'] = path_obj.get_suggestion_count()

    return stats


def get_translation_stats(path_obj, path_stats):
    """Returns a list of statistics for ``path_obj`` ready to be displayed.

    :param path_obj: A :cls:`pootle_app.models.directory.Directory` or
                     :cls:`pootle_store.models.Store` object.
    :param path_stats: A dictionary of raw stats, as returned by
                       :func:`pootle_misc.stats.get_raw_stats`.
    """
    stats = []

    def make_stats_dict(title, state, filter_url=True):
        filter_name = filter_url and state or None
        return {
            'title': title,
            'words': ungettext('<a href="%(url)s">%(num)d word</a>',
                               '<a href="%(url)s">%(num)d words</a>',
                               path_stats['untranslated']['words'],
                               {'url': path_obj.get_translate_url(
                                   state=filter_name,
                                ),
                                'num': path_stats[state]['words']}),
            'percentage': _("%(num)d%%",
                            {'num': path_stats[state]['percentage']}),
            'units': ungettext("(%(num)d string)",
                               "(%(num)d strings)",
                               path_stats[state]['units'],
                               {'num': path_stats[state]['units']})
        }

    if path_stats['total']['units'] > 0:
        stats.append(make_stats_dict(_("Total"), 'total', filter_url=False))

    if path_stats['translated']['units'] > 0:
        stats.append(make_stats_dict(_("Translated"), 'translated'))

    if path_stats['fuzzy']['units'] > 0:
        stats.append(make_stats_dict(_("Needs work"), 'fuzzy'))

    if path_stats['untranslated']['units'] > 0:
        stats.append(make_stats_dict(_("Untranslated"), 'untranslated'))

    return stats


def get_path_summary(path_obj, path_stats, latest_action):
    """Returns a list of sentences to be displayed for each ``path_obj``."""
    summary = []
    incomplete = []
    suggestions = []

    if path_obj.is_dir:
        summary.append(
            ungettext("This folder has %(num)d word, %(percentage)d%% of "
                "which is translated.",
                "This folder has %(num)d words, %(percentage)d%% of "
                "which are translated.",
                path_stats['total']['words'],
                {
                    'num': path_stats['total']['words'],
                    'percentage': path_stats['translated']['percentage']
                })
        )
    else:
        summary.append(
            ungettext("This file has %(num)d word, %(percentage)d%% of "
                "which is translated.",
                "This file has %(num)d words, %(percentage)d%% of "
                "which are translated.",
                path_stats['total']['words'],
                {
                    'num': path_stats['total']['words'],
                    'percentage': path_stats['translated']['percentage']
                })
        )

    tp = path_obj.translation_project
    project = tp.project
    language = tp.language

    # Build URL for getting more summary information for the current path
    url_args = [language.code, project.code, path_obj.path]
    url_path_summary_more = reverse('tp.path_summary_more', args=url_args)

    summary.append(u''.join([
        ' <a id="js-path-summary" data-target="js-path-summary-more" '
        'href="%s">' % url_path_summary_more,
        force_unicode(_(u'Expand details')),
        '</a>'
    ]))


    if path_stats['untranslated']['words'] > 0 or path_stats['fuzzy']['words'] > 0:
        num_words = path_stats['untranslated']['words'] + path_stats['fuzzy']['words']
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
            goal = Goal.get_most_important_incomplete_for_path(pootle_path)

            if goal is not None:
                goal_words = goal.get_incomplete_words_in_path(pootle_path)
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


def stats_message_raw(version, stats):
    """Builds a message of statistics used in VCS actions."""
    return "%s: %d of %d strings translated (%d need review)." % \
           (version, stats.get("translated", 0), stats.get("total", 0),
            stats.get("fuzzy", 0))


def stats_message(version, stats):
    """Builds a localized message of statistics used in VCS actions."""
    # Translators: 'type' is the type of VCS file: working, remote,
    # or merged copy.
    return ungettext(u"%(type)s: %(translated)d of %(total)d string translated "
                            u"(%(fuzzy)d need review).",
                     u"%(type)s: %(translated)d of %(total)d strings translated "
                            u"(%(fuzzy)d need review).",
                     stats.get("total", 0),
                     {
                          'type': version,
                          'translated': stats.get("translated", 0),
                          'total': stats.get("total", 0),
                          'fuzzy': stats.get("fuzzy", 0)
                     })


def stats_descriptions(quick_stats):
    """Provides a dictionary with two textual descriptions of the work
    outstanding.
    """
    total_words = quick_stats["total"]["words"]
    untranslated = quick_stats["untranslated"]["words"]
    fuzzy = quick_stats["fuzzy"]["words"]
    todo_words = untranslated + fuzzy

    todo_text = ungettext("%d word needs attention",
                          "%d words need attention", todo_words, todo_words)

    untranslated_tooltip = ungettext("%d word untranslated",
                                     "%d words untranslated",
                                     untranslated, untranslated)
    fuzzy_tooltip = ungettext("%d word needs review",
                              "%d words need review", fuzzy, fuzzy)
    todo_tooltip = u"<br>".join([untranslated_tooltip, fuzzy_tooltip])

    return {
        'total_words': total_words,
        'todo_words': todo_words,
        'todo_text': todo_text,
        'todo_tooltip': todo_tooltip,
    }
