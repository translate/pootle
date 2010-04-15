#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from difflib import SequenceMatcher
from django.utils.safestring import mark_safe

from django import template
from django.utils.translation import ugettext as _
from django.core.exceptions import  ObjectDoesNotExist

from pootle_store.models import Unit
from pootle_profile.models import get_profile
from pootle_misc.templatetags.cleanhtml import fancy_escape

register = template.Library()

def find_altsrcs(unit, profile, store=None, project=None):
    store = store or unit.store
    project = project or store.translation_project.project
    altsrcs = Unit.objects.filter(unitid_hash=unit.unitid_hash, store__name=store.name,
                                 store__translation_project__project=project,
                                 store__translation_project__language__in=profile.alt_src_langs.all(),
                                 target_length__gt=0).select_related('store', 'store__translation_project', 'store__translation_project__language')
    return altsrcs

def highlight_diffs(old, new):
    """Highlights the differences between old and new. The differences
    are highlighted such that they show what would be required to
    transform old into new.
    """

    textdiff = ""
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, old, new).get_opcodes():
        if tag == 'equal':
            textdiff += fancy_escape(old[i1:i2])
        if tag == "insert":
            textdiff += '<span class="translate-diff-insert">%s</span>' % fancy_escape(new[j1:j2])
        if tag == "delete":
            textdiff += '<span class="translate-diff-delete">%s</span>' % fancy_escape(old[i1:i2])
        if tag == "replace":
            # We don't show text that was removed as part of a change:
            #textdiff += "<span>%s</span>" % fance_escape(a[i1:i2])}
            textdiff += '<span class="translate-diff-replace">%s</span>' % fancy_escape(new[j1:j2])
    return mark_safe(textdiff)

def get_sugg_list(unit):
    """get suggested translations for given unit with the localized
    title string for each suggestions"""
    # this function is only needed to avoid translations strings with
    # variables in templates, since template translation is not safe
    # and might fail on livetranslation
    sugg_list = []
    for i, sugg in enumerate(unit.get_suggestions().iterator()):
        title = _("Suggestion %(i)d by %(user)s:", {'i': i, 'user': sugg.user})
        sugg_list.append((sugg, title))
    return sugg_list

@register.filter('stat_summary')
def stat_summary(store):
    stats = store.getquickstats()
    # The translated word counts
    words_percent = stats['translatedsourcewords'] / (stats['totalsourcewords'] or 1) * 100
    word_stats = _("Words Translated: %(translated)d/%(total)d - %(translatedpercent)d%%",
                   {"translated": stats['translatedsourcewords'],
                    "total": stats['totalsourcewords'],
                    "translatedpercent": words_percent})
    word_stats = '<span class="word-statistics">%s</span>' % word_stats

    # The translated unit counts
    strings_percent = stats['translated'] / (stats['total'] or 1) * 100
    string_stats = _("Strings Translated: %(translated)d/%(total)d - %(translatedpercent)d%%",
                          {"translated": stats['translated'],
                           "total": stats['total'],
                          "translatedpercent": strings_percent})
    string_stats = '<span class="string-statistics">%s</span>' % string_stats
    # The whole string of stats
    return mark_safe('%s &nbsp;&nbsp; %s' % (word_stats, string_stats))

@register.filter('pluralize_source')
def pluralize_source(unit):
    if unit.hasplural():
        return [(0, unit.source.strings[0], _('Singular')), (1, unit.source.strings[1], _('Plural'))]
    else:
        return [(0, unit.source, None)]

@register.filter('pluralize_target')
def pluralize_target(unit, nplurals=None):
    if unit.hasplural():
        if nplurals is None:
            try:
                nplurals = unit.store.translation_project.language.nplurals
            except ObjectDoesNotExist:
                pass
        forms = []
        if nplurals is None:
            for i, target in enumerate(unit.target.strings):
                forms.append((i, target, _('Plural Form %d', i)))
        else:
            for i in range(nplurals):
                try:
                    target = unit.target.strings[i]
                except IndexError:
                    target = ''
                forms.append((i, target, _('Plural Form %d', i)))
        return forms
    else:
        return [(0, unit.target, None)]

@register.filter('pluralize_diff_sugg')
def pluralize_diff_sugg(sugg):
    unit = sugg.unit
    if unit.hasplural():
        forms = []
        for i, target in enumerate(sugg.target.strings):
            forms.append((i, target, highlight_diffs(unit.target.strings[i], target), _('Plural Form %d', i)))
        return forms
    else:
        return [(0, sugg.target, highlight_diffs(unit.target, sugg.target), None)]


@register.inclusion_tag('unit/edit.html', takes_context=True)
def render_unit_edit(context, form):
    request = context['request']
    profile = get_profile(context['user'])
    unit = form.instance
    store = context['store']
    translation_project = context['translation_project']
    project = translation_project.project
    template_vars = {'unit': unit,
                     'form': form,
                     'store': store,
                     'language': context['language'],
                     "cantranslate": context['cantranslate'],
                     "cansuggest": context['cansuggest'],
                     "canreview": context['canreview'],
                     'altsrcs': find_altsrcs(unit, profile, store=store, project=project),
                     "suggestions": get_sugg_list(unit),
                     }
    return template_vars

@register.inclusion_tag('unit/view.html', takes_context=True)
def render_unit_view(context, unit, show_comments=False):
    request = context['request']
    template_vars = {'unit': unit,
                     'language': context['language'],
                     'show_comments': show_comments,
                     }
    return template_vars
