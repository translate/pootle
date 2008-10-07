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

import time
from datetime import datetime
from lxml     import objectify
from StringIO import StringIO

from spelt.models.source import Source

class TestSource:
    """Unit test for the Source model class."""

    xml1 = StringIO("""
        <source id="1" date="1212555224" import_user_id="4">
            <name>Test Source 1</name>
            <filename>testsrc1.txt</filename>
            <description>A fictitious source for testing purposes</description>
        </source>""")

    xml2 = StringIO("""
        <source id="2" date="1212555925" import_user_id="2">
            <name>Test Source 2</name>
            <filename>testsrc2.txt</filename>
            <description>Another fictitious source for testing purposes</description>
        </source>""")

    def __init__(self):
        self.elem1 = objectify.parse(TestSource.xml1).getroot()
        self.elem2 = objectify.parse(TestSource.xml2).getroot()

    def test_create_no_xml_attribs(self):
        """
        Test creation of a simple Source object with its own constructor.
        XML attributes (first 3 arguments) only.
        """
        now = str(int( time.mktime(datetime.now().timetuple()) ))
        s = Source(id=101, date=now, import_user_id=2)

        assert s.id == 101
        assert s.date == now
        assert s.import_user_id == 2
        assert isinstance(s.name, objectify.NoneElement)
        assert isinstance(s.filename, objectify.NoneElement)
        assert isinstance(s.description, objectify.NoneElement)

    def test_create_no_xml_values(self):
        """
        Test creation of a simple Source object with its own constructor.
        XML child nodes (last 3 arguments) only.
        """
        s = Source(name='New Source', filename='newsrc.txt', desc='This is the newest source!!!')

        assert s.import_user_id == 0
        assert s.name == 'New Source'
        assert s.filename == 'newsrc.txt'
        assert s.description == 'This is the newest source!!!'

    def test_create_with_xml(self):
        """
        Test creation of a Source instance by using the create_from_elem()
        factory method.
        """
        s1 = Source(elem=self.elem1)
        s2 = Source(elem=self.elem2)

        assert s1.name == 'Test Source 1'
        assert s1.filename == 'testsrc1.txt'
        assert s1.description == 'A fictitious source for testing purposes'
        assert s1.id == 1
        assert s1.date == '1212555224'
        assert s1.import_user_id == 4

        assert s2.name == 'Test Source 2'
        assert s2.filename == 'testsrc2.txt'
        assert s2.description == 'Another fictitious source for testing purposes'
        assert s2.id == 2
        assert s2.date == '1212555925'
        assert s2.import_user_id == 2


if __name__ == "__main__":
    t = TestSource()
    t.test_create_no_xml_attribs()
    t.test_create_no_xml_values()
    t.test_create_with_xml()
    t.test_import_user_id_alias()
