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
"""Monkeypatching fixtures."""


# HACKISH: monkeypatching decorator here, should be cleaner to do it in a
# fixture, but pytest's `monkeypatch` decorator is function-scoped, and by
# the time it's run the decorators have already been applied to the
# functions, therefore the patching has no effect
from _pytest.monkeypatch import monkeypatch

mp = monkeypatch()
mp.setattr('django.utils.functional.cached_property', property)
