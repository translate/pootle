#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Spelt.
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

from lxml     import objectify
from StringIO import StringIO

from spelt.models.pos import PartOfSpeech

class TestPartOfSpeech(object):
    """Unit test for the PartOfSpeech model class."""

    xml1 = StringIO("""
        <part_of_speech id="1">
            <shortcut>n1</shortcut>
            <name>Noun, ôrdinary</name>
            <remarks>Examples include "hond", "boom" and "appel"</remarks>
        </part_of_speech>""")

    xml2 = StringIO("""
        <part_of_speech id="2">
            <shortcut>v1sp</shortcut>
            <name>Verb, 1st person singular, present tense</name>
            <remarks></remarks>
        </part_of_speech>""")

    def test_create_no_xml(self):
        """
        Test creation of a simple PartOfSpeech object with its own constructor.
        """
        pos = PartOfSpeech('Noun, ordinary', 'n1', 'Simple noun', 1)

        assert pos.id == 1
        assert pos.shortcut == 'n1'
        assert pos.name == 'Noun, ordinary'
        assert pos.remarks == 'Simple noun'

    def test_create_from_xml(self):
        """
        Test creation of a PartOfSpeech instance by using the create_from_elem()
        factory method.
        """
        elem1 = objectify.parse(TestPartOfSpeech.xml1).getroot()
        elem2 = objectify.parse(TestPartOfSpeech.xml2).getroot()
        pos1 = PartOfSpeech(elem=elem1)
        pos2 = PartOfSpeech(elem=elem2)

        assert pos1.id == 1 and pos2.id == 2
        assert pos1.shortcut == 'n1' and pos2.shortcut == 'v1sp'
        assert pos1.name == u'Noun, ôrdinary'
        assert pos2.name == 'Verb, 1st person singular, present tense'
        assert len(str(pos1.remarks)) == 43 and pos2.remarks == ''

if __name__ == "__main__":
    p = PartOfSpeech()
    p.test_create_no_xml()
    p.test_create_from_xml()
