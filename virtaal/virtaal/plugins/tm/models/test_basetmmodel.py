#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of Virtaal.
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

from basetmmodel import unescape_html_entities

def test_unescape_html_entities():
    """Test the unescaping of &amp; and &#39; type HTML escapes"""
    assert unescape_html_entities("This &amp; That") == "This & That"
    assert unescape_html_entities("&#39;n Vertaler") == "'n Vertaler"
    assert unescape_html_entities("Copyright &copy; 2009 Virtaa&#7741;") == u"Copyright © 2009 Virtaaḽ"
