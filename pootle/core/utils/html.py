# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from lxml.html import rewrite_links as lxml_rewrite_links


def rewrite_links(input_html, callback, **kwargs):
    """Thin wrapper around lxml's `rewrite_links()` that prevents extra HTML
    markup from being produced when there's no root tag present in the
    input HTML.

    This is needed as a workaround for #3889, and it simply wraps the input
    text within `<div>...</div>` tags.
    """
    return lxml_rewrite_links(u'<div>%s</div>' % input_html,
                              callback, **kwargs)
