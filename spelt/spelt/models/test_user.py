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

from spelt.models.user import User

class TestUser:
    """Unit test for the User model class."""

    xml = StringIO("""
        <user id="5">
            <name>Bongani Buthelêzi</name>
            <data>
                <entry>
                    <key>Title</key><value>Professor</value>
                </entry>
            </data>
        </user>""")

    def test_create_no_xml(self):
        """
        Test creation of a simple User object with its own constructor.
        """
        u = User(id=1)
        assert u.id == 1
        u = User(id=2, name=u'Unicode Náme')
        assert u.name == u'Unicode Náme'
        u = User('ASCII Name', 3)
        assert u.id == 3 and u.name == 'ASCII Name'

    def test_create_from_xml(self):
        """
        Test creation of a User instance by using the create_from_elem()
        factory method.
        """
        elem = objectify.parse(TestUser.xml).getroot()
        u = User(elem=elem)

        assert u.id == 5
        assert u.name == u'Bongani Buthelêzi'

if __name__ == "__main__":
    t = TestUser()
    t.test_create_no_xml()
    t.test_create_from_xml()
