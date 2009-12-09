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

from datetime import datetime
from lxml     import etree, objectify
from StringIO import StringIO

from spelt.models.surface_form import SurfaceForm

class TestSurfaceForm(object):
    """Unit test for the SurfaceForm model class."""

    xml1 = StringIO("""
        <surface_form id="10" user_id="1" date="123" source_id="11" root_id="111">
            <value>koeie</value>
            <status>classified</status>
        </surface_form>""")

    xml2 = StringIO("""
        <surface_form id="20" user_id="2" date="321" source_id="22" root_id="222">
            <value>varkagtighede</value>
            <status>ignored</status>
        </surface_form>""")

    def test_create_no_xml(self):
        """
        Test creation of a simple SurfaceForm object with its own constructor.
        """
        sf = SurfaceForm(u'verkoeílikheid', 'rejected')
        assert sf.value  == u'verkoeílikheid'
        assert sf.status == 'rejected'

        sf = SurfaceForm(u'varkieş', 'todo', 3, 30, datetime.fromtimestamp(0), 33, 333)
        assert sf.value     == u'varkieş'
        assert sf.status    == 'todo'
        assert sf.id        == 3
        assert sf.user_id   == 30
        assert sf.date      == "0"
        assert sf.source_id == 33
        assert sf.root_id   == 333

    def test_create_from_xml(self):
        """
        Test creation of a SurfaceForm instance by using the create_from_elem()
        factory method.
        """
        elem1 = objectify.parse(TestSurfaceForm.xml1).getroot()
        elem2 = objectify.parse(TestSurfaceForm.xml2).getroot()
        sf1 = SurfaceForm(elem=elem1)
        sf2 = SurfaceForm(elem=elem2)

        assert sf1.value     == u'koeie'
        assert sf1.status    == 'classified'
        assert sf1.user_id   == 1
        assert sf1.date      == '123'
        assert sf1.source_id == 11
        assert sf1.root_id   == 111

        assert sf2.value     == unicode('varkagtighede')
        assert sf2.status    == 'ignored'
        assert sf2.user_id   == 2
        assert sf2.date      == '321'
        assert sf2.source_id == 22
        assert sf2.root_id   == 222
