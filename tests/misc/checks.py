#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
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

import pytest

from translate.filters.checks import FilterFailure
from pootle_misc.checks import ENChecker

checker = ENChecker()


def do_test(check, tests):
    for str1, str2, state in tests:
        info = "check('%s', '%s') == %s" % (str1, str2, state)
        try:
            assert (state == check(str1, str2)), info

        except FilterFailure as e:

            assert (not state), info


def test_dollar_sign_check():
    check = checker.dollar_sign_placeholders

    tests = [
        (u'$1 aa $2', u'$1 dd $2', True),
        (u'$1 aa $2', u'$1dd$2', True),
    ]

    do_test(check, tests)


def test_double_quotes_in_tags():
    check = checker.double_quotes_in_tags
    tests = [
        (u'foo bar', u'FOO BAR', True),
        (u'foo "bar"', u'"FOO" <BAR>', True),
        (u'foo "bar"', u'FOO <BAR>', True),
        (u'foo <a href="bar">foo bar</a>',
         u'FOO <a href="BAR">FOO BAR</a>', True),
        (u'"foo" <a href="bar">"foo" bar</a>',
         u'FOO <a href="BAR">FOO BAR</a>', True),
        (u'<a href="bar>foo bar</a>', u'FOO BAR', False),
        (u'foo bar', u'<a href="BAR">FOO BAR</a>', True),
        (u'foo bar', u'<a href="BAR>FOO BAR</a>', False),
        (u'foo <a href="bar">foo bar</a>',
         u'FOO <a href="BAR>FOO BAR</a>', False),
        (u'foo <a href="bar">foo bar</a>',
         u'FOO <a href=\'BAR\'>FOO BAR</a>', False),
        (u'foo <a href="<?php echo("bar");?>">foo bar</a>',
         u'FOO <a href="<?php echo("BAR");?>">FOO BAR</a>', True),
        (u'foo <a href="<?php echo("bar");?>">foo bar</a>',
         u'FOO <a href="<?php echo(\'BAR\');?>">FOO BAR</a>', False),
    ]

    do_test(check, tests)


def test_unescaped_ampersands():
    check = checker.unescaped_ampersands
    tests = [
        (u'A and B', u'A и B', True),
        (u'A and B', u'A & B', True),
        (u'A and B', u'A &amp; B', True),
        (u'A & B', u'A и B', True),
        (u'A & B', u'A & B', True),
        (u'A &amp; B', u'A и B', True),
        (u'A &amp; B', u'A & B', False),
        (u'A &amp; B', u'A &amp; B', True),
        (u'A &amp; B &amp; C', u'A &amp; B & C', False),
        (u'A &amp; B & C', u'A и B и C', True),
        (u'A &amp; B & C', u'A & B & C', False),
        (u'A &amp; B & C', u'A &amp; B &amp; C', True),
        (u'A &amp; B & C', u'A &amp; B & C', False),
        (u"A &quot; B &amp; C", u"A &quot; B &amp; C", True),
    ]

    do_test(check, tests)


def test_incorrectly_escaped_ampersands():
    check = checker.incorrectly_escaped_ampersands
    tests = [
        (u'A and B', u'A и B', True),
        (u'A and B', u'A & B', True),
        (u'A and B', u'A &amp; B', True),
        (u'A and B and C', u'A &amp; B & C ', False),
        (u'A & B', u'A и B', True),
        (u'A & B', u'A & B', True),
        (u'A & B', u'A &amp; B', False),
        (u'A & B & C', u'A &amp; B & C', False),
        (u'A &amp; B', u'A и B', True),
        (u'A &amp; B', u'A &amp; B', True),
        (u'A &amp; B & C', u'A и B и C', True),
        (u'A &amp; B & C', u'A &amp; B &amp; C', False),
        (u"A &quot; B &amp; C", u"A &quot; B &amp; C", True),
    ]

    do_test(check, tests)


def test_mustache_placeholders():
    check = checker.mustache_placeholders
    tests = [
        (u'{foo}bar', u'{foo}BAR', True),
        (u'{{foo}}bar', u'{{foo}}BAR', True),
        (u'{{{foo}}}bar', u'{{{foo}}}BAR', True),

        (u'{{foo}}bar{{foobar}}', u'{{foobar}}BAR{{foo}}', True),

        (u'{1, foo}bar{{foobar}}', u'{1, foo}BAR{{foobar}}', True),
        (u'bar {1, foo}bar{{foobar}}', u'BAR {1, FOO}BAR{{foobar}}', False),

        (u'{foo}bar', u'{Foo}BAR', False),
        (u'{{foo}}bar', u'{{Foo}}BAR', False),
        (u'{{{foo}}}bar', u'{{{Foo}}}BAR', False),

        (u'{{foo}}bar', u'{foo}}BAR', False),
        (u'{{{foo}}}bar', u'{{foo}}}BAR', False),
        (u'{{foo}}bar', u'{{foo}BAR', False),
        (u'{{{foo}}}bar', u'{{{foo}}BAR', False),

        (u'{{#a}}a{{/a}}', u'{{#a}}A{{a}}', False),
        (u'{{a}}a{{/a}}', u'{{a}}A{{a}}', False),
        (u'{{#a}}a{{/a}}', u'{{#a}}A', False),
        (u'{{#a}}a{{/a}}', u'{{#a}}A{{/s}}', False),

        (u'{{a}}a{{/a}}', u'{{a}}A', False),
        (u'{{a}}a{{/a}}', u'{{a}}A{{a}}', False),
        (u'{{a}}a{{/a}}', u'{{a}}A{{/s}}', False),
        (u'{{#a}}a{{/a}}', u'{{a}}A{{/a#}}', False),
        (u'{{#a}}a{{/a}}', u'{{# a}}A{{/ a}}', False),
    ]

    do_test(check, tests)


def test_mustache_placeholder_pairs():
    check = checker.mustache_placeholder_pairs
    tests = [
        (u'{{#a}}a{{/a}}', u'{{#a}}A{{/a}}', True),

        (u'{{#a}}a', u'{{#a}}A', False),
        (u'{{#a}}a{{/a}}', u'{{#a}}A', False),
        (u'{{#a}}a{{/a}}', u'{{#a}}A{{#a}}', False),
        (u'{{#a}}a{{/a}}', u'{{#a}}A{{a}}', False),
        (u'{{#a}}a{{/a}}', u'{{/a}}A{{#a}}', False),
        (u'{{#a}}a{{/a}}', u'{{a}}A{{/a}}', False),
        (u'{{#a}}a{{/a}}', u'{{#a}}A{{/s}}', False),

        (u'{{#a}}a{{/a}}', u'{{a}}A{{/a#}}', False),
        (u'{{#a}}a{{/a}}', u'{{#a}}A{{/ a}}', False),
    ]

    do_test(check, tests)


def test_mustache_like_placeholder_pairs():
    check = checker.mustache_like_placeholder_pairs
    tests = [
        (u'a', u'A', True),
        (u'{{a}}a', u'{{a}}A', True),
        (u'{{a}}a{{/a}}', u'{{a}}A{{/a}}', True),
        (u'a {{#a}}a{{/a}}', u'A {{#a}}A{{/a}}', True),

        (u'foo {{a}}a{{/a}}', u'FOO {{/a}}A{{a}}', False),
        (u'foo {{a}}a{{/a}}', u'FOO {{a}}A{{/s}}', False),
        (u'foo {{a}}a{{/a}}', u'FOO {{a}}A{{/s}}', False),
        (u'foo {{a}}a{{/a}}', u'FOO {{a}}A{{/ a}}', False),
    ]

    do_test(check, tests)


def test_unbalanced_curly_braces():
    check = checker.unbalanced_curly_braces

    tests = [
        (u'', u'', True),
        (u'{a}', u'{a}', True),
        (u'{{a}}', u'{{a}', False),
    ]

    do_test(check, tests)


def test_tags_differ():
    check = checker.tags_differ
    tests = [
        (u'a', u'A', True),
        (u'<a href="">a</a>', u'<a href="">a</a>', True),
        (u'<a href="">a</a>', u'<a href="">a<a>', False),
        (u'<a class="a">a</a>', u'<b class="b">a</b>', False),
    ]

    do_test(check, tests)
