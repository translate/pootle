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

from pootle_misc.util import add_percentages


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
    quick_stats = add_percentages(path_obj.getquickstats())

    stats = {
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


def get_translate_actions(path_obj, path_stats):
    """Returns a list of translation action links to be displayed for each ``path_obj``."""
    incomplete = []
    suggestions = []

    if path_stats['untranslated']['words'] > 0 or path_stats['fuzzy']['words'] > 0:
        num_words = path_stats['untranslated']['words'] + path_stats['fuzzy']['words']
        incomplete.extend([
            u'<a class="continue-translation" href="%(url)s">' % {
                    'url': path_obj.get_translate_url(state='incomplete')
                },
            ungettext(u'Continue translation: <span class="counter">%(num)d word left</span>',
                      u'Continue translation: <span class="counter">%(num)d words left</span>',
                      num_words,
                      {'num': num_words, }),
        ])
    else:
        incomplete.extend([
            u'<a class="translation-complete" href="%(url)s">' % {
                    'url': path_obj.get_translate_url(state='all')
                },
            force_unicode(_('Translation is complete <span class="counter">view all</span>')),
        ])

    incomplete.append(u'</a>')


    if path_stats['suggestions'] > 0:
        suggestions.append(u'<a class="review-suggestions" href="%(url)s">' % {
            'url': path_obj.get_translate_url(state='suggestions')
        })
        suggestions.append(
            ungettext(u'Review suggestion: <span class="counter">%(num)d left</span>',
                      u'Review suggestions: <span class="counter">%(num)d left</span>',
                      path_stats['suggestions'],
                      {'num': path_stats['suggestions'], })
        )
        suggestions.append(u'</a>')

    return [u''.join(incomplete), u''.join(suggestions)]


def stats_message_raw(version, stats):
    """Builds a message of statistics used in VCS actions."""
    return "%s: %d of %d strings translated (%d fuzzy)." % \
           (version, stats.get("translated", 0), stats.get("total", 0),
            stats.get("fuzzy", 0))


def stats_message(version, stats):
    """Builds a localized message of statistics used in VCS actions."""
    # Translators: 'type' is the type of VCS file: working, remote,
    # or merged copy.
    return ungettext(u"%(type)s: %(translated)d of %(total)d string translated "
                            u"(%(fuzzy)d fuzzy).",
                     u"%(type)s: %(translated)d of %(total)d strings translated "
                            u"(%(fuzzy)d fuzzy).",
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
