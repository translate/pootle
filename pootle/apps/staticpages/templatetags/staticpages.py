# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import template
from django.urls import reverse

from ..models import LegalPage


register = template.Library()


class LegalPageNode(template.Node):

    def __init__(self, context_name):
        self.context_name = context_name

    def render(self, context):
        lps = LegalPage.objects.live().all()

        context[self.context_name] = lps
        return ''


@register.tag
def get_legalpages(parser, token):
    """
    Retrieves all active LegalPage objects.
    Populates the template context with them in a variable
    whose name is defined by the ``as`` clause.

    Syntax::

        {% get_legalpages as context_name %}
    """

    bits = token.split_contents()
    syntax_message = ("%(tag_name)s expects a syntax of %(tag_name)s "
                      "as context_name" %
                      dict(tag_name=bits[0]))

    if len(bits) == 3:

        if bits[1] != 'as':
            raise template.TemplateSyntaxError(syntax_message)
        context_name = bits[2]

        return LegalPageNode(context_name)
    else:
        raise template.TemplateSyntaxError(syntax_message)


@register.tag
def staticpage_url(parser, token):
    """Returns the internal URL for a static page based on its virtual path.

    Syntax::

        {% staticpage_url 'virtual/path' %}
    """
    bits = token.split_contents()
    syntax_message = ("%(tag_name)s expects a syntax of %(tag_name)s "
                      "'virtual/path'" %
                      dict(tag_name=bits[0]))
    quote_message = "%s tag's argument should be in quotes" % bits[0]

    if len(bits) == 2:
        virtual_path = bits[1]

        if (not (virtual_path[0] == virtual_path[-1] and
                 virtual_path[0] in ('"', "'"))):
            raise template.TemplateSyntaxError(quote_message)

        return StaticPageURLNode(virtual_path[1:-1])

    raise template.TemplateSyntaxError(syntax_message)


class StaticPageURLNode(template.Node):

    def __init__(self, virtual_path):
        self.virtual_path = virtual_path

    def render(self, context):
        return reverse('pootle-staticpages-display', args=[self.virtual_path])
