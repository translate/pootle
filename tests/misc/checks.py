#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.filters.checks import FilterFailure
from pootle_misc.checks import ENChecker

checker = ENChecker()


def do_test(check, tests):
    for str1, str2, state in tests:
        info = "check('%s', '%s') == %s" % (str1, str2, state)
        try:
            assert (state == check(str1, str2)), info
        except FilterFailure:
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
        (u'foobar', u'{foo}BAR', True),
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


def test_percent_brace_placeholders():
    check = checker.percent_brace_placeholders
    tests = [
        (u'{foo}% bar', u'%{foo} BAR', True),
        (u'%{foo} bar', u'%{foo} BAR', True),
        (u'%{foo} bar', u'% {foo} BAR', False),
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


def test_broken_entities():
    check = checker.broken_entities
    tests = [
        (u'foo bar?<br>&#13;',
         u'FOO BAR<br>&#13;', True),
        (u'foo &#65535;',
         u'FOO &#65535;', True),
        (u'foo &#xff;',
         u'FOO &#xff;', True),
        (u'foo &#65535;',
         u'FOO &#65536;', False),
        (u'foo &nbsp;',
         u'FOO &nbsp', False),
    ]

    do_test(check, tests)


def test_date_format():
    check = checker.date_format
    tests = [
        (u"EEE, MMM d h:mm a", u"EEE, MMM d HH:mm", True),
        (u"EEE, MMM", u"EEEMMM", False),
        (u"yyyy.MM.dd G 'at' HH:mm:ss z", u"yyyy.MM.dd G 'в' HH:mm:ss z", True),
        (u"EEE, MMM d, ''yy", u"dd-MM-yy", True),
        (u"h:mm a", u"dd-MM-yy", True),
        (u"hh 'o''clock' a, zzzz", u"dd-MM-yy", True),
        (u"K:mm a, z", u"dd-MM-yy", True),
        (u"yyyyy.MMMMM.dd GGG hh:mm aaa", u"dd-MM-yy", True),
        (u"EEE, d MMM yyyy HH:mm:ss Z", u"dd-MM-yy", True),
        (u"yyyy-MM-dd'T'HH:mm:ss.SSSZ", u"dd-MM-yy", True),
        (u"yyyy-MM-dd'T'HH:mm:ss.SSSXXX", u"dd-MM-yy", True),
        (u"YYYY-'W'ww-u", u"dd-MM-yy", True),

        # if a string isn't a date_format string the check should be skipped
        (u"yyMMddHHmmssZ", u"what ever 345", True),
        (u"F", u"what ever 345", True),
        (u"M", u"what ever 345", True),
        (u"S", u"what ever 345", True),
        (u"W", u"what ever 345", True),
    ]

    do_test(check, tests)
