#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Spelt
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

def label(code):
    if isinstance(code, str):
        return ('~', 0, code)    # built-in functions ('~' sorts at the end)
    else:
        return '%s %s:%d' % (code.co_name, code.co_filename, code.co_firstlineno)


class KCacheGrind(object):
    def __init__(self, profiler):
        self.data = profiler.getstats()
        self.out_file = None

    def output(self, out_file):
        self.out_file = out_file
        print >> out_file, 'events: Ticks'
        self._print_summary()
        for entry in self.data:
            self._entry(entry)

    def _print_summary(self):
        max_cost = 0
        for entry in self.data:
            totaltime = int(entry.totaltime * 1000)
            max_cost = max(max_cost, totaltime)
        print >> self.out_file, 'summary: %d' % (max_cost,)

    def _entry(self, entry):
        out_file = self.out_file
        code = entry.code
        inlinetime = int(entry.inlinetime * 1000)
        #print >> out_file, 'ob=%s' % (code.co_filename,)
        if isinstance(code, str):
            print >> out_file, 'fi=~'
        else:
            print >> out_file, 'fi=%s' % (code.co_filename,)
        print >> out_file, 'fn=%s' % (label(code),)
        if isinstance(code, str):
            print >> out_file, '0 ', inlinetime
        else:
            print >> out_file, '%d %d' % (code.co_firstlineno, inlinetime)
        # recursive calls are counted in entry.calls
        if entry.calls:
            calls = entry.calls
        else:
            calls = []
        if isinstance(code, str):
            lineno = 0
        else:
            lineno = code.co_firstlineno
        for subentry in calls:
            self._subentry(lineno, subentry)
        print >> out_file

    def _subentry(self, lineno, subentry):
        out_file = self.out_file
        code = subentry.code
        totaltime = int(subentry.totaltime * 1000)
        #print >> out_file, 'cob=%s' % (code.co_filename,)
        print >> out_file, 'cfn=%s' % (label(code),)
        if isinstance(code, str):
            print >> out_file, 'cfi=~'
            print >> out_file, 'calls=%d 0' % (subentry.callcount,)
        else:
            print >> out_file, 'cfi=%s' % (code.co_filename,)
            print >> out_file, 'calls=%d %d' % (
                subentry.callcount, code.co_firstlineno)
        print >> out_file, '%d %d' % (lineno, totaltime)


def profilefunc(profile_file, func, *args):
    import cProfile

    profiler = cProfile.Profile()
    profiler.runcall(func, *args)

    k_cache_grind = KCacheGrind(profiler)
    k_cache_grind.output(profile_file)

    profile_file.close()
