# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest


WORDCOUNT_TESTS = OrderedDict()


WORDCOUNT_TESTS['string_with_repeated_newlines'] = {
    "string": ("There is a woman in town by the name of Elsie Dolban. She is "
               "eccentric, and that has caused some of the villagers to "
               "condemn her. I'm interested in *your* opinion of "
               "her.\n\nSpeak to Inquisitor Roche, he has strong opinions in "
               "this matter."),
    "ttk": 44,
    "pootle": 45,
}
WORDCOUNT_TESTS['simple_string'] = {
    "string": ("There is a woman in town by the name of Elsie Dolban."),
    "ttk": 12,
    "pootle": 12,
}
WORDCOUNT_TESTS['dots'] = {
    "string": ("Before.After"),
    "ttk": 2,
    "pootle": 1,
}
WORDCOUNT_TESTS['escaped_tags'] = {
    "string": ("&lt;b>"),
    "ttk": 1,
    "pootle": 0,
}
WORDCOUNT_TESTS['xml_tags'] = {
    "string": ("<b>"),
    "ttk": 0,
    "pootle": 0,
}
WORDCOUNT_TESTS['xml_tags_with_attributes'] = {
    "string": ('<p class="whatever">'),
    "ttk": 0,
    "pootle": 0,
}
WORDCOUNT_TESTS['java_format'] = {
    "string": ("\23 said"),
    "ttk": 2,
    "pootle": 1,
}
WORDCOUNT_TESTS['template_format'] = {
    "string": ("Hi ${name}"),
    "ttk": 2,
    "pootle": 1,
}
WORDCOUNT_TESTS['android_format'] = {
    "string": ("%3$n"),
    "ttk": 1,
    "pootle": 0,
}
WORDCOUNT_TESTS['sprintf'] = {
    "string": ("I am %s."),
    "ttk": 3,
    "pootle": 2,
}
WORDCOUNT_TESTS['objective_c'] = {
    "string": ("Hi %@"),
    "ttk": 1,
    "pootle": 1,
}
WORDCOUNT_TESTS['dollar_sign'] = {
    "string": ("$name$"),
    "ttk": 1,
    "pootle": 0,
}
WORDCOUNT_TESTS['newlines'] = {
    "string": ("\n\n"),
    "ttk": 0,
    "pootle": 0,
}
WORDCOUNT_TESTS['escape_sequences'] = {
    "string": ("\r\n\t"),
    "ttk": 0,
    "pootle": 0,
}
WORDCOUNT_TESTS['xml_entities'] = {
    "string": ("&dash;"),
    "ttk": 1,
    "pootle": 0,
}
WORDCOUNT_TESTS['numeric_xml_entities'] = {
    "string": ("&#123;"),
    "ttk": 1,
    "pootle": 0,
}
WORDCOUNT_TESTS['product_names'] = {
    "string": ("Evernote International"),
    "ttk": 2,
    "pootle": 0,
}
WORDCOUNT_TESTS['shortcuts'] = {
    "string": ("Ctrl+A"),
    "ttk": 1,
    "pootle": 0,
}
WORDCOUNT_TESTS['shortcuts_modifiers'] = {
    "string": ("Ctrl+"),
    "ttk": 1,
    "pootle": 0,
}


@pytest.fixture(params=WORDCOUNT_TESTS.keys())
def wordcount_names(request):
    return request.param
