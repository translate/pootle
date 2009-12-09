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

from spelt.models.root import Root

class TestRoot:
    """Unit test for the Source model class."""

    xml1 = StringIO("""
        <root id="1" pos_id="11" user_id="111" date="1212555224">
            <value>koeï</value>
            <remarks>Ä cow.</remarks>
        </root>""")

    xml2 = StringIO("""
        <root id="2" pos_id="22" user_id="222" date="1212555925">
            <value>boom</value>
        </root>""")

    def test_create_no_xml(self):
        """
        Test creation of a simple Root object with its own constructor.
        """
        r = Root()
        now = str(int( time.mktime(datetime.now().timetuple()) ))
        # r.id not tested because it should be automagically determined by
        # the voodoo in IDManager
        assert r.value   == u''
        assert r.remarks == u''
        assert r.pos_id  == 0
        assert r.user_id == 0
        assert r.date    == now
        del r

        r = Root(u'roöt', u'remarkş', 1, 11, 111, datetime.fromtimestamp(123456))
        assert r.value   == u'roöt'
        assert r.remarks == u'remarkş'
        assert r.id      == 1
        assert r.pos_id  == 11
        assert r.user_id == 111
        assert r.date    == '123456'
        del r

    def test_create_with_xml(self):
        """
        Test creation of a Root instance by using the create_from_elem()
        factory method.
        """
        elem1 = objectify.parse(TestRoot.xml1).getroot()
        elem2 = objectify.parse(TestRoot.xml2).getroot()
        r1 = Root(elem=elem1)
        r2 = Root(elem=elem2)

        assert r1.value   == u'koeï'
        assert r1.remarks == u'Ä cow.'
        assert r1.id      == 1
        assert r1.pos_id  == 11
        assert r1.user_id == 111
        assert r1.date    == "1212555224"

        assert r2.value   == u'boom'
        assert r2.remarks == u''
        assert r2.id      == 2
        assert r2.pos_id  == 22
        assert r2.user_id == 222
        assert r2.date    == "1212555925"

        del r1
        del r2
