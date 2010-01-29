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

from django import template
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext

from pootle_store.models import Unit

register = template.Library()

def pluralize_source(unit):
    if unit.hasplural():
        return [(unit.source.strings[0], _('Singular')), (unit.source.strings[1], _('Plural'))]
    else:
        return [(unit.source, None)]

def pluralize_target(unit, nplurals=None):
    if unit.hasplural():
        forms = []
        if nplurals is None:
            for i, target in enumerate(unit.target.strings):
                forms.append((target, _('Plural Form %d', i)))
        else:
            for i in range(nplurals):
                try:
                    target = unit.target.strings[i]
                except IndexError:
                    target = ''
                forms.append((target, _('Plural Form %d', i)))
        return forms
    else:
        return [(unit.target, None)]

def find_altsrcs(unit, profile):
    altsrcs = []
    path_fragments = unit.store.pootle_path.split('/')
    for language in profile.alt_src_langs.iterator():
        try:
            path_fragments[1] = language.code
            pootle_path = '/'.join(path_fragments)
            altunit = Unit.objects.get(unitid_hash=unit.unitid_hash, target_length__gt=0,
                                       store__pootle_path=pootle_path)
            altsrcs.append((language, altunit, pluralize_target(altunit)))
        except Unit.DoesNotExist:
            pass
    return altsrcs

@register.inclusion_tag('unit/source.html', takes_context=True)
def render_source(context, unit, editable=False):
    template_vars = {'unit': unit,
                     'editable': editable,
                     'sources': pluralize_source(unit),
                     }
    if editable:
        template_vars['altsrcs'] = find_altsrcs(unit, context['pootle_profile'])

    return template_vars

@register.inclusion_tag('unit/target.html', takes_context=True)
def render_target(context, unit):
    template_vars = {'unit': unit,
                     'targets': pluralize_target(unit),
                     'language': context['pootle_context']['language'],
                     }
    suggcount = unit.get_suggestions().count()
    template_vars['suggcount'] = suggcount
    if suggcount:
        template_vars['suggtext'] = ungettext('%(count)s suggestion', '%(count)s suggestions', suggcount, {'count': suggcount})
    return template_vars

@register.inclusion_tag('unit/developer_notes.html', takes_context=True)
def render_developer_notes(context, unit, editable=False):
    template_vars = {'unit': unit,
                    }
    return template_vars

@register.inclusion_tag('unit/translator_notes.html', takes_context=True)
def render_translator_notes(context, unit, editable=False):
    template_vars = {'unit': unit,
                     'language': context['pootle_context']['language'],
                     'editable': editable,
                     }
    return template_vars

