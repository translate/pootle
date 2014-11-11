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

def test_dollar_sign_check():
    check = checker.dollar_sign_placeholders

    tests = [
        (u'$1 aa $2', u'$1 dd $2', True),
        (u'$1 aa $2', u'$1dd$2', True),
    ]

    for str1, str2, state in tests:
        info = "check('%s', '%s') == %s" % (str1, str2, state)
        try:
            assert (state == check(str1, str2)), info

        except FilterFailure as e:

            assert (not state), info


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
        (u'foo <a href="bar">foo bar</a>',
         u'FOO <a href="BAR>FOO BAR</a>', False),
        (u'foo <a href="bar">foo bar</a>',
         u'FOO <a href=\'BAR\'>FOO BAR</a>', False),
        (u'foo <a href="<?php echo("bar");?>">foo bar</a>',
         u'FOO <a href="<?php echo("BAR");?>">FOO BAR</a>', True),
        (u'foo <a href="<?php echo("bar");?>">foo bar</a>',
         u'FOO <a href="<?php echo(\'BAR\');?>">FOO BAR</a>', False),
    ]

    for str1, str2, state in tests:
        info = "check('%s', '%s') == %s" % (str1, str2, state)
        try:
            assert (state == check(str1, str2)), info

        except FilterFailure as e:

            assert (not state), info

