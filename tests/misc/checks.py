#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from translate.filters.checks import FilterFailure

from pootle_misc.checks import ENChecker

try:
    from plurr import Plurr
except ImportError:
    Plurr = None


checker = ENChecker()


def assert_check(check, source_string, target_string, should_skip, **kwargs):
    """Runs `check` and asserts whether it should be skipped or not for the
    given `source_string` and `target_string`.

    :param check: Checker function.
    :param source_string: Source string.
    :param target_string: Target string.
    :param should_skip: Whether the check should be skipped.
    """
    try:
        assert should_skip == check(source_string, target_string, **kwargs)
    except FilterFailure:
        assert not should_skip


@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u'$1 aa $2', u'$1 dd $2', True),
    (u'$1 aa $2', u'$1dd$2', True),
])
def test_dollar_sign_check(source_string, target_string, should_skip):
    check = checker.dollar_sign_placeholders
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u'foo bar', u'FOO BAR', True),
    (u'foo "bar"', u'"FOO" <BAR>', True),
    (u'foo "bar"', u'FOO <BAR>', True),
    (u'foo <a href="bar">foo bar</a>',
     u'FOO <a href="BAR">FOO BAR</a>', True),
    (u'"foo" <a href="bar">"foo" bar</a>', u'FOO <a href="BAR">FOO BAR</a>', True),
    (u'<a href="bar>foo bar</a>', u'FOO BAR', False),
    (u'foo bar', u'<a href="BAR">FOO BAR</a>', True),
    (u'foo bar', u'<a href="BAR>FOO BAR</a>', False),
    (u'foo <a href="bar">foo bar</a>', u'FOO <a href="BAR>FOO BAR</a>', False),
    (u'foo <a href="bar">foo bar</a>', u'FOO <a href=\'BAR\'>FOO BAR</a>', False),
    (u'foo <a href="<?php echo("bar");?>">foo bar</a>',
     u'FOO <a href="<?php echo("BAR");?>">FOO BAR</a>', True),
    (u'foo <a href="<?php echo("bar");?>">foo bar</a>',
     u'FOO <a href="<?php echo(\'BAR\');?>">FOO BAR</a>', False),
])
def test_double_quotes_in_tags(source_string, target_string, should_skip):
    check = checker.double_quotes_in_tags
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
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
])
def test_unescaped_ampersands(source_string, target_string, should_skip):
    check = checker.unescaped_ampersands
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
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
])
def test_incorrectly_escaped_ampersands(source_string, target_string, should_skip):
    check = checker.incorrectly_escaped_ampersands
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u'NAME_COUNT', u'name_count', False),
    (u'NAME_COUNT', u'NaMe_CouNT', False),
    (u'NAME_COUNT', u'NAME_COUNT', True),

    (u'NAME6_', u'name_', False),
    (u'NAME6_', u'name_count', False),
    (u'NAME6_', u'NAME7_', False),
    (u'NAME6_', u'NAME6_', True),

    # Ignore the check altogether for Plurr-like source strings
    (u'{:{BAR}}', u'Foo', True),
    (u'{:{:a|b}|c}', u'Foo', True),
    (u'{FOO:{BAR}}', u'Foo', True),
    (u'{FOO:{BAR:a|b}|c}', u'Foo', True),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'', True),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo', True),
])
def test_uppercase_placeholders(source_string, target_string, should_skip):
    check = checker.uppercase_placeholders
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
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

    # Ignore the check altogether for Plurr-like source strings
    (u'{:{BAR}}', u'Foo', True),
    (u'{:{:a|b}|c}', u'Foo', True),
    (u'{FOO:{BAR}}', u'Foo', True),
    (u'{FOO:{BAR:a|b}|c}', u'Foo', True),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'', True),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo', True),
])
def test_mustache_placeholders(source_string, target_string, should_skip):
    check = checker.mustache_placeholders
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u'{foo}% bar', u'%{foo} BAR', True),
    (u'%{foo} bar', u'%{foo} BAR', True),
    (u'%{foo} bar', u'% {foo} BAR', False),
])
def test_percent_brace_placeholders(source_string, target_string, should_skip):
    check = checker.percent_brace_placeholders
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
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
])
def test_mustache_placeholder_pairs(source_string, target_string, should_skip):
    check = checker.mustache_placeholder_pairs
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u'a', u'A', True),
    (u'{{a}}a', u'{{a}}A', True),
    (u'{{a}}a{{/a}}', u'{{a}}A{{/a}}', True),
    (u'a {{#a}}a{{/a}}', u'A {{#a}}A{{/a}}', True),

    (u'foo {{a}}a{{/a}}', u'FOO {{/a}}A{{a}}', False),
    (u'foo {{a}}a{{/a}}', u'FOO {{a}}A{{/s}}', False),
    (u'foo {{a}}a{{/a}}', u'FOO {{a}}A{{/s}}', False),
    (u'foo {{a}}a{{/a}}', u'FOO {{a}}A{{/ a}}', False),
])
def test_mustache_like_placeholder_pairs(source_string, target_string, should_skip):
    check = checker.mustache_like_placeholder_pairs
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u'', u'', True),
    (u'{a}', u'{a}', True),
    (u'{{a}}', u'{{a}', False),

    # Ignore the check altogether for Plurr-like source strings
    (u'{:{BAR}}', u'Foo', True),
    (u'{:{:a|b}|c}', u'Foo', True),
    (u'{FOO:{BAR}}', u'Foo', True),
    (u'{FOO:{BAR:a|b}|c}', u'Foo', True),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'', True),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo', True),
])
def test_unbalanced_curly_braces(source_string, target_string, should_skip):
    check = checker.unbalanced_curly_braces
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u'a', u'A', True),
    (u'<a href="">a</a>', u'<a href="">a</a>', True),
    (u'<a href="">a</a>', u'<a href="">a<a>', False),
    (u'<a class="a">a</a>', u'<b class="b">a</b>', False),
])
def test_tags_differ(source_string, target_string, should_skip):
    check = checker.tags_differ
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u'&Foo', u'Foo', False),
    (u'&Foo', u'_Foo', False),
    (u'&Foo', u'^Foo', False),

    (u'^Foo', u'Foo', False),
    (u'^Foo', u'_Foo', False),
    (u'^Foo', u'&Foo', False),

    (u'_Foo', u'Foo', False),
    (u'_Foo', u'&Foo', False),
    (u'_Foo', u'^Foo', False),

    (u'&Foo', u'&foo', True),
    (u'&Foo', u'bar&foo', True),

    (u'^Foo', u'^foo', True),
    (u'^Foo', u'bar^foo', True),

    (u'_Foo', u'_foo', True),
    (u'_Foo', u'bar_foo', True),

    # Ignore the check altogether for Plurr-like source strings
    (u'{:{BAR}}', u'Foo', True),
    (u'{:{:a|b}|c}', u'Foo', True),
    (u'{FOO:{BAR}}', u'Foo', True),
    (u'{FOO:{BAR:a|b}|c}', u'Foo', True),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'', True),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo', True),
])
def test_accelerators(source_string, target_string, should_skip):
    check = checker.accelerators
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u'foo bar?<br>&#13;', u'FOO BAR<br>&#13;', True),
    (u'foo &#65535;', u'FOO &#65535;', True),
    (u'foo &#xff;', u'FOO &#xff;', True),
    (u'foo &#65535;', u'FOO &#65536;', False),
    (u'foo &nbsp;', u'FOO &nbsp', False),
])
def test_broken_entities(source_string, target_string, should_skip):
    check = checker.broken_entities
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u"EEE, MMM d h:mm a", u"EEE, MMM d HH:mm", True),
    (u"EEE, MMM", u"EEEMMM", False),
    (u"yyyy.MM.dd G 'at' HH:mm:ss z",
     u"yyyy.MM.dd G 'в' HH:mm:ss z", True),
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
])
def test_date_format(source_string, target_string, should_skip):
    check = checker.date_format
    assert_check(check, source_string, target_string, should_skip)


@pytest.mark.skipif(Plurr is None, reason='Plurr library not installed')
@pytest.mark.parametrize('source_string, target_string, should_skip', [
    (u'', u'', True),
    (u'Foo bar', u'', True),
    (u'Foo {bar}', u'', True),

    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'', True),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo {BAR_PLURAL:foo}', True),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo {BAR_PLURAL:foo|{BAR}}', True),

    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo {BAR_PLURAL:foo', False),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo BAR_PLURAL:foo}', False),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo {BAR_PLURAL:{BAR|foo}', False),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo {BAR_PLURAL:BAR}|foo}', False),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo {BAR_PLURAL:{BAR}|foo}}', False),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo {BAR_PLURAL:{BAR}|{foo}', False),
    (u'Foo {BAR_PLURAL:Zero|{BAR}}', u'Foo {BAR_PLURAL:{{{BAR}}|foo}', False),
])
def test_plurr_format(source_string, target_string, should_skip):
    check = checker.plurr_format
    assert_check(check, source_string, target_string, should_skip,
                 language_code='ru')
