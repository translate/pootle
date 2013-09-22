#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django import template

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
