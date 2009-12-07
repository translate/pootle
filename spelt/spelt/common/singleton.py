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
#
# This file incorporates work covered by the following copyright:
#
#   Copyright (c) 2007, Antonio Valentino
#   Obtained from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/102187
#   which is licensed under the Python license.

class SingletonMeta(type):
    """Singleton metaclass.

        This class is not meant to be instantiated, but to be used as a
        __metaclass__ by other classes. Doing so applies the Singleton design
        pattern to that class.
        
        Taken from last comment at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/102187"""

    def __init__(cls, name, bases, dic):
        super(SingletonMeta, cls).__init__(name, bases, dic)
        cls.instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            #print 'Creating new Singleton instance of class %s' % (cls.__name__)
            cls.instance = super(SingletonMeta, cls).__call__(*args, **kwargs)

        return cls.instance
