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

from diff_match_patch import diff_match_patch
from translate.misc.multistring import multistring
from translate.storage.placeables import parse as parse_placeables
from translate.storage.placeables.interfaces import BasePlaceable

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import stringfilter
from django.template.loaders.filesystem import Loader
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from pootle_store.fields import list_empty
from pootle_store.placeables import PLACEABLE_PARSERS, PLACEABLE_DESCRIPTIONS


register = template.Library()


@register.filter
@stringfilter
def highlight_placeables(text):
    """Wrap placeables to easily distinguish and manipulate them."""
    output = u""

    # Get a flat list of placeables and StringElem instances.
    flat_items = parse_placeables(text, PLACEABLE_PARSERS).flatten()

    for item in flat_items:
        if isinstance(item, BasePlaceable):
            # It is a placeable, so highlight it.

            class_name = item.__class__.__name__
            placeable = unicode(item)  # String representation for placeable.

            # CSS class used to highlight the placeable.
            css_class = {
                'PootleEscapePlaceable': "highlight-escape",
                'PootleSpacesPlaceable': "translation-space",
                'PootleTabEscapePlaceable': "highlight-escape",
                'NewlinePlaceable': "highlight-escape",
            }.get(class_name, "placeable")

            # Some placeables require changing the representation in order to
            # correctly display them on the translation editor.

            def replace_whitespace(string):
                fancy_space = '&nbsp;'
                if string.startswith(' '):
                    return fancy_space * len(string)
                return string[0] + fancy_space * (len(string) - 1)

            content = {
                'PootleEscapePlaceable': u'\\\\',
                'PootleTabEscapePlaceable': u'\\t',
                'PootleSpacesPlaceable': replace_whitespace(placeable),
                'NewlinePlaceable': {
                        u'\r\n': u'\\r\\n<br/>\n',
                        u'\r': u'\\r<br/>\n',
                        u'\n': u'\\n<br/>\n',
                    }.get(placeable),
                'XMLEntityPlaceable': placeable.replace('&', '&amp;'),
                'XMLTagPlaceable': placeable.replace('<', '&lt;') \
                                            .replace('>', '&gt;'),
            }.get(class_name, placeable)

            # Provide a description for the placeable using a tooltip.
            description = PLACEABLE_DESCRIPTIONS.get(class_name,
                                                     _("Unknown placeable"))

            output += (u'<span class="%s js-editor-copytext js-placeable" '
                       u'title="%s">%s</span>') % (css_class, description,
                                                   content)
        else:
            # It is not a placeable, so just concatenate to output string.
            output += escape(item)

    return mark_safe(output)


IMAGE_URL_RE = re.compile("(https?://[^\s]+\.(png|jpe?g|gif))")
@register.filter
def image_urls(text):
    """Return a list of image URLs extracted from `text`."""
    return map(lambda x: x[0], IMAGE_URL_RE.findall(text))


ESCAPE_RE = re.compile('<[^<]*?>|\\\\|\r\n|[\r\n\t&<>]')
def fancy_escape(text):
    """Replace special chars with entities, and highlight XML tags and
    whitespaces.
    """
    def replace(match):
        escape_highlight = ('<span class="highlight-escape '
                            'js-editor-copytext">%s</span>')
        submap = {
            '\r\n': (escape_highlight % '\\r\\n') + '<br/>\n',
            '\r': (escape_highlight % '\\r') + '<br/>\n',
            '\n': (escape_highlight % '\\n') + '<br/>\n',
            '\t': (escape_highlight % '\\t'),
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '\\': (escape_highlight % '\\\\'),
        }
        try:
            return submap[match.group()]
        except KeyError:
            html_highlight = ('<span class="highlight-html '
                              'js-editor-copytext">&lt;%s&gt;</span>')
            return html_highlight % fancy_escape(match.group()[1:-1])

    return ESCAPE_RE.sub(replace, text)


def call_highlight(old, new):
    """Call diff highlighting code only if the target is set.

    Otherwise, highlight as a normal unit.
    """
    if isinstance(old, multistring):
        old_value = old.strings
    else:
        old_value = old
    if list_empty(old_value):
        return highlight_placeables(new)
    else:
        return highlight_diffs(old, new)


differencer = diff_match_patch()
def highlight_diffs(old, new):
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
