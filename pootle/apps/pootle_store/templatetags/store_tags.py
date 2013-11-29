#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
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

import re

from translate.misc.multistring import multistring

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.template.loaders.app_directories import Loader
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from pootle_misc.templatetags.cleanhtml import fancy_escape, fancy_highlight
from pootle_store.fields import list_empty


register = template.Library()


IMAGE_URL_RE = re.compile("(https?://[^\s]+\.(png|jpe?g|gif))")


@register.filter
def image_urls(text):
    """Return a list of image URLs extracted from `text`."""
    return map(lambda x: x[0], IMAGE_URL_RE.findall(text))


def call_highlight(old, new):
    """Call diff highlighting code only if the target is set.

    Otherwise, highlight as a normal unit.
    """
    if isinstance(old, multistring):
        old_value = old.strings
    else:
        old_value = old
    if list_empty(old_value):
        return fancy_highlight(new)
    else:
        return highlight_diffs(old, new)


def _google_highlight_diffs(old, new):
    """Highlight the differences between old and new."""

    textdiff = u""  # To store the final result.
    removed = u""  # The removed text that we might still want to add.
    diff = differencer.diff_main(old, new)
    differencer.diff_cleanupSemantic(diff)
    for op, text in diff:
        if op == 0:  # Equality.
            if removed:
                textdiff += ('<span class="diff-delete">%s</span>' %
                             fancy_escape(removed))
                removed = u""
            textdiff += fancy_escape(text)
        elif op == 1:  # Insertion.
            if removed:
                # This is part of a substitution, not a plain insertion. We
                # will format this differently.
                textdiff += ('<span class="diff-replace">%s</span>' %
                             fancy_escape(text))
                removed = u""
            else:
                textdiff += ('<span class="diff-insert">%s</span>' %
                             fancy_escape(text))
        elif op == -1:  # Deletion.
            removed = text
    if removed:
        textdiff += ('<span class="diff-delete">%s</span>' %
                     fancy_escape(removed))
    return mark_safe(textdiff)


def _difflib_highlight_diffs(old, new):
    """Highlight the differences between old and new.

    The differences are highlighted such that they show what would be required
    to transform old into new.
    """
    textdiff = ""
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, old, new).get_opcodes():
        if tag == 'equal':
            textdiff += fancy_escape(old[i1:i2])
        if tag == "insert":
            textdiff += ('<span class="diff-insert">%s</span>' %
                         fancy_escape(new[j1:j2]))
        if tag == "delete":
            textdiff += ('<span class="diff-delete">%s</span>' %
                         fancy_escape(old[i1:i2]))
        if tag == "replace":
            # We don't show text that was removed as part of a change:
            #textdiff += "<span>%s</span>" % fance_escape(a[i1:i2])}
            textdiff += ('<span class="diff-replace">%s</span>' %
                         fancy_escape(new[j1:j2]))
    return mark_safe(textdiff)


try:
    from translate.misc.diff_match_patch import diff_match_patch
    differencer = diff_match_patch()
    highlight_diffs = _google_highlight_diffs
except ImportError:
    from difflib import SequenceMatcher
    highlight_diffs = _difflib_highlight_diffs


@register.filter('pluralize_source')
def pluralize_source(unit):
    if unit.hasplural():
        count = len(unit.source.strings)
        if count == 1:
            return [(0, unit.source.strings[0], "%s+%s" % (_('Singular'),
                                                           _('Plural')))]
        elif count == 2:
            return [(0, unit.source.strings[0], _('Singular')),
                    (1, unit.source.strings[1], _('Plural'))]
        else:
            forms = []
            for i, source in enumerate(unit.source.strings):
                forms.append((i, source, _('Plural Form %d', i)))
            return forms
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
            if i < len(unit.target.strings):
                forms.append((i, target, call_highlight(unit.target.strings[i],
                                                        target),
                              _('Plural Form %d', i)))
            else:
                forms.append((i, target, call_highlight('', target),
                              _('Plural Form %d', i)))
        return forms
    else:
        return [(0, sugg.target, call_highlight(unit.target, sugg.target),
                 None)]


@register.tag(name="include_raw")
def do_include_raw(parser, token):
    """Perform a raw template include.

    This means to include the template without parsing context, just dump the
    template in.

    Source: http://djangosnippets.org/snippets/1684/
    """
    bits = token.split_contents()
    if len(bits) != 2:
        excp_msg = ("%r tag takes one argument: the name of the template to "
                    "be included" % bits[0])
        raise template.TemplateSyntaxError(excp_msg)

    template_name = bits[1]
    if (template_name[0] in ('"', "'") and
        template_name[-1] == template_name[0]):
        template_name = template_name[1:-1]

    template_loader = Loader()
    source, path = template_loader.load_template_source(template_name)

    return template.TextNode(source)
