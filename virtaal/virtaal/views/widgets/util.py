#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

__all__ = ['forall_widgets']

import gtk

from virtaal.support.simplegeneric import generic


@generic
def get_children(widget):
    return []

@get_children.when_type(gtk.Container)
def get_children_container(widget):
    return widget.get_children()

def forall_widgets(f, widget):
    f(widget)
    for child in get_children(widget):
        forall_widgets(f, child)

