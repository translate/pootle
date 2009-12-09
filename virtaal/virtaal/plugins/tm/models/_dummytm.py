#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

from basetmmodel import BaseTMModel


class TMModel(BaseTMModel):
    """This is a dummy (testing) translation memory model."""

    __gtype_name__ = 'DummyTMModel'
    display_name = _('Dummy TM provider for testing')
    description = _('A translation memory suggestion providers that is only useful for testing')

    # INITIALIZERS #
    def __init__(self, internal_name, controller):
        self.internal_name = internal_name
        super(TMModel, self).__init__(controller)


    # METHODS #
    def query(self, tmcontroller, query_str):
        tm_matches = []
        tm_matches.append({
            'source': 'This match has no "quality" field',
            'target': u'Hierdie woordeboek het geen "quality"-veld nie.',
            'tmsource': 'DummyTM'
        })
        tm_matches.append({
            'source': query_str.lower(),
            'target': query_str.upper(),
            'quality': 100,
            'tmsource': 'DummyTM'
        })
        reverse_str = list(query_str)
        reverse_str.reverse()
        reverse_str = u''.join(reverse_str)
        tm_matches.append({
            'source': reverse_str.lower(),
            'target': reverse_str.upper(),
            'quality': 32,
            'tmsource': 'DummyTM'
        })

        self.emit('match-found', query_str, tm_matches)
