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

from django.utils.translation import ugettext_lazy as _, ungettext

from pootle_misc.util import nice_percentage


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
                               path_stats[state],
                               {'url': path_obj.get_translate_url(
                                   state=filter_name,
                                ),
                               'num': path_stats[state]}),
            'percentage': _("%(num)d%%",
                            {'num': nice_percentage(path_stats['total'] /
                                                    path_stats[state] * 100)}),
        }

    if path_stats['total'] > 0:
        stats.append(make_stats_dict(_("Total"), 'total', filter_url=False))

    if path_stats['translated'] > 0:
        stats.append(make_stats_dict(_("Translated"), 'translated'))

    if path_stats['fuzzy'] > 0:
        stats.append(make_stats_dict(_("Needs work"), 'fuzzy'))

    if path_stats['untranslated'] > 0:
        stats.append(make_stats_dict(_("Untranslated"), 'untranslated'))

    return stats


def get_translate_actions(path_obj, path_stats, checks_stats):
    """Returns a list of translation action links to be displayed for ``path_obj``."""

    result = []
    complete = path_stats['untranslated']['words'] == 0 and path_stats['fuzzy']['words'] == 0

    if not complete:
        num_words = path_stats['untranslated']['words'] + path_stats['fuzzy']['words']

        result.append(
            u'<a class="continue-translation" href="%(url)s">%(text)s</a>' % {
                'url': path_obj.get_translate_url(state='incomplete'),
                'text': ungettext(u'<span class="caption">Continue translation:</span> <span class="counter">%(num)d word left</span>',
                                  u'<span class="caption">Continue translation:</span> <span class="counter">%(num)d words left</span>',
                                  num_words,
                                  {'num': num_words, }),
            }
        )

    if path_stats['suggestions'] > 0:
        result.append(
            u'<a class="review-suggestions" href="%(url)s">%(text)s</a>' % {
                'url': path_obj.get_translate_url(state='suggestions'),
                'text': ungettext(u'<span class="caption">Review suggestion:</span> <span class="counter">%(num)d left</span>',
                                  u'<span class="caption">Review suggestions:</span> <span class="counter">%(num)d left</span>',
                                  path_stats['suggestions'],
                                  {'num': path_stats['suggestions'], })
            }
        )

    # 100 is the value of 'CRITICAL' checks category in Translate Toolkit,
    # see translate/filters/decorators.py, Category.CRITICAL
    CRITICAL = 100L

    if CRITICAL in checks_stats:
        keys = checks_stats[CRITICAL].keys()
        keys.sort()

        count = 0;
        for checkname in keys:
            count += checks_stats[CRITICAL][checkname]

        checks = ",".join(keys)

        result.append(
            u'<a class="fix-errors" href="%(url)s">%(text)s</a>' % {
                'url': path_obj.get_translate_url(check=checks),
                'text': ungettext(u'<span class="caption">Fix critical error:</span> <span class="counter">%(num)d left</span>',
                                  u'<span class="caption">Fix critical errors:</span> <span class="counter">%(num)d left</span>',
                                  count,
                                  {'num': count, })
            }
        )

    if complete:
        result.append(
            u'<a class="translation-complete" href="%(url)s">%(text)s</a>' % {
                'url': path_obj.get_translate_url(state='all'),
                'text': _('<span class="caption">Translation complete:</span> <span class="counter">view all</span>')
            }
        )

    return result

def stats_message_raw(version, total, translated, fuzzy):
    """Builds a message of statistics used in VCS actions."""
    return "%s: %d of %d strings translated (%d fuzzy)." % \
           (version, translated, total, fuzzy)


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

# TODO delete
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
