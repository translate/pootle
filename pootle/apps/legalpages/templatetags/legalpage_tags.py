#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
#
# This file is part of Pootle.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django import template

from legalpages.models import LegalPage


register = template.Library()


class LegalPageNode(template.Node):

    def __init__(self, context_name, on_register=False):
        self.context_name = context_name
        self.on_register = on_register

    def render(self, context):
        lps = LegalPage.objects.filter(active=True)

        if self.on_register:
            lps = lps.filter(display_on_register=True)

        context[self.context_name] = lps
        return ''


@register.tag
def get_legalpages(parser, token):
    """
    Retrieves all active LegalPage objects.
    Populates the template context with them in a variable
    whose name is defined by the ``as`` clause.

    An optional ``reg`` clause can be added at the end to retrieve
    only the objects that have the ``display_on_register`` bit set.

    Syntax::

        {% get_legalpages as context_name [reg]%}
    """

    bits = token.split_contents()
    syntax_message = ("%(tag_name)s expects a syntax of %(tag_name)s "
                       "as context_name" %
                       dict(tag_name=bits[0]))

    if len(bits) >= 3 and len(bits) <= 4:

        if bits[1] != 'as':
            raise template.TemplateSyntaxError(syntax_message)
        context_name = bits[2]

        on_register = False
        if len(bits) == 4:
            on_register = True

        return LegalPageNode(context_name, on_register)
    else:
        raise template.TemplateSyntaxError(syntax_message)
