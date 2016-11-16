# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re

from django import template
from django.core.exceptions import ObjectDoesNotExist

from pootle.core.utils.templates import get_template_source
from pootle.i18n.gettext import ugettext as _


register = template.Library()


IMAGE_URL_RE = re.compile("(https?://[^\s]+\.(png|jpe?g|gif))", re.IGNORECASE)


@register.filter
def image_urls(text):
    """Return a list of image URLs extracted from `text`."""
    return map(lambda x: x[0], IMAGE_URL_RE.findall(text))


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

    source, __ = get_template_source(template_name)

    return template.base.TextNode(source)
