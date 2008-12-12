#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from threading import Lock

from translate.misc.context import with_
from translate.misc.contextlib import contextmanager

cache_templates = True

prefs = None

def make_atomic_manager():
    lock = Lock()

    @contextmanager
    def atomic_manager():
        lock.acquire()
        yield lock
        lock.release()

    return atomic_manager

_po_tree = None
_po_tree_manager = make_atomic_manager()

def get_po_tree():
    def with_block(lock):
        global _po_tree
        
        if _po_tree is None:
            from Pootle import potree
            _po_tree = potree.POTree(prefs)
        return _po_tree

    return with_(_po_tree_manager(), with_block)

