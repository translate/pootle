#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re

from diff_match_patch import diff_match_patch
from translate.misc.multistring import multistring
from translate.storage.placeables import general

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from pootle.core.utils.templates import get_template_source
from pootle_store.fields import list_empty


register = template.Library()


IMAGE_URL_RE = re.compile("(https?://[^\s]+\.(png|jpe?g|gif))", re.IGNORECASE)


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


WHITESPACE_RE = re.compile('^ +| +$|[\r\n\t] +| {2,}')


def fancy_spaces(text):
    """Highlight spaces to make them easily visible."""
    def replace(match):
        fancy_space = '<span class="translation-space"> </span>'
        if match.group().startswith(' '):
            return fancy_space * len(match.group())
        return match.group()[0] + fancy_space * (len(match.group()) - 1)
    return WHITESPACE_RE.sub(replace, text)


PUNCTUATION_RE = general.PunctuationPlaceable().regex


def fancy_punctuation_chars(text):
    """Wrap punctuation chars found in the ``text`` around tags."""
    def replace(match):
        fancy_special_char = ('<span class="highlight-punctuation '
                              'js-editor-copytext">%s</span>')
        return fancy_special_char % match.group()

    return PUNCTUATION_RE.sub(replace, text)


@register.filter
@stringfilter
def fancy_highlight(text):
    return mark_safe(fancy_punctuation_chars(fancy_spaces(fancy_escape(text))))


def call_highlight(old, new):
    """Calls diff highlighting code only if the target is set.
    Otherwise, highlight as a normal unit.
    """
    if isinstance(old, multistring):
        old_value = old.strings
    else:
        old_value = old

    if list_empty(old_value):
        return fancy_highlight(new)

    return highlight_diffs(old, new)


differencer = diff_match_patch()


def highlight_diffs(old, new):
    """Highlight the differences between old and new."""

    textdiff = u""  # to store the final result
    removed = u""  # the removed text that we might still want to add
    diff = differencer.diff_main(old, new)
    differencer.diff_cleanupSemantic(diff)
    for op, text in diff:
        if op == 0:  # equality
            if removed:
                textdiff += '<span class="diff-delete">%s</span>' % \
                    fancy_escape(removed)
                removed = u""
            textdiff += fancy_escape(text)
        elif op == 1:  # insertion
            if removed:
                # this is part of a substitution, not a plain insertion. We
                # will format this differently.
                textdiff += '<span class="diff-replace">%s</span>' % \
                    fancy_escape(text)
                removed = u""
            else:
                textdiff += '<span class="diff-insert">%s</span>' % \
                    fancy_escape(text)
        elif op == -1:  # deletion
            removed = text
    if removed:
        textdiff += '<span class="diff-delete">%s</span>' % \
            fancy_escape(removed)
    return mark_safe(textdiff)


@register.filter('pluralize_source')
def pluralize_source(unit):
    if not unit.hasplural():
        return [(0, unit.source, None)]

    count = len(unit.source.strings)
    if count == 1:
        return [(0, unit.source.strings[0], "%s+%s" % (_('Singular'),
                                                       _('Plural')))]

    if count == 2:
        return [(0, unit.source.strings[0], _('Singular')),
                (1, unit.source.strings[1], _('Plural'))]

    forms = []
    for i, source in enumerate(unit.source.strings):
        forms.append((i, source, _('Plural Form %d', i)))
    return forms


@register.filter('pluralize_target')
def pluralize_target(unit, nplurals=None):
    if not unit.hasplural():
        return [(0, unit.target, None)]

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


@register.filter('pluralize_diff_sugg')
def pluralize_diff_sugg(sugg):
    unit = sugg.unit
    if not unit.hasplural():
        return [
            (0, sugg.target, call_highlight(unit.target, sugg.target), None)
        ]

    forms = []
    for i, target in enumerate(sugg.target.strings):
        if i < len(unit.target.strings):
            sugg_text = unit.target.strings[i]
        else:
            sugg_text = ''

        forms.append((
            i, target, call_highlight(sugg_text, target),
            _('Plural Form %d', i)
        ))

    return forms


@register.tag(name="include_raw")
def do_include_raw(parser, token):
    """
    Performs a template include without parsing the context, just dumps
    the template in.
    Source: http://djangosnippets.org/snippets/1684/
    """
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(
            "%r tag takes one argument: the name of the template "
            "to be included" % bits[0]
        )

    template_name = bits[1]
    if (template_name[0] in ('"', "'") and
            template_name[-1] == template_name[0]):
        template_name = template_name[1:-1]

    source, path = get_template_source(template_name)

    return template.base.TextNode(source)
