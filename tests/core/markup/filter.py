# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.markup.filters import apply_markup_filter


@pytest.mark.parametrize('markdown_text, expected_html, config', [
    # Blank
    ('', '', {}),
    (' \t', '', {}),
    # Standard markdown
    ('Paragraph', '<p>Paragraph</p>', {}),
    ('## Header', '<h2>Header</h2>', {}),
    ('* List', '<ul><li>List</li></ul>', {}),
    ('<hr>', '<hr>', {}),
    # Accept img tags since markdown is rubbish at images
    ('Show icon <img alt="image" src="pic.png">',
     '<p>Show icon <img alt="image" src="pic.png"></p>', {}),
    # Escape a <script> tag
    ('Bad hacker <script>alert("Bang!")</script>',
     '<p>Bad hacker &lt;script&gt;alert("Bang!")&lt;/script&gt;</p>', {}),
    # Extra tags
    ('Unknown <tag>Escaped</tag>',
     '<p>Unknown &lt;tag&gt;Escaped&lt;/tag&gt;</p>', {}),
    ('Extra <tag>Included</tag>',
     '<p>Extra <tag>Included</tag></p>',
     {'clean': {
         'extra_tags': ['tag'],
     }}),
    # Extra attributes
    ('Unknown <a attr="no">Escaped</a>',
     '<p>Unknown <a>Escaped</a></p>', {}),
    ('Extra <a attr="yes">Included</a>',
     '<p>Extra <a attr="yes">Included</a></p>',
     {'clean': {
         'extra_attrs': {'a': ['attr']},
     }}),
    # Extra styles
    ('Unknown <a style="color: remove;">Escaped</a>',
     '<p>Unknown <a>Escaped</a></p>', {}),
    ('Extra <a style="color: accept;">Included</a>',
     '<p>Extra <a style="color: accept;">Included</a></p>',
     {'clean': {
         'extra_attrs': {'*': ['style']},
         'extra_styles': ['color'],
     }}),
])
def test_apply_markup_filter(settings, markdown_text, expected_html, config):
    settings.POOTLE_MARKUP_FILTER = ('markdown', config)
    output_html = apply_markup_filter(markdown_text)
    output_html = output_html[5:-6]  # Remove surrounding <div>...</div>
    output_html = output_html.replace('\n', '')  # Remove pretty print newlines
    assert output_html == expected_html
