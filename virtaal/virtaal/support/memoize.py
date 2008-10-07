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

__all__ = ['memoize', 'invalidates_memoization']

memoize_table = {}

def get_full_fn_name(f):
    return "%s.%s" % (f.__module__,  f.__name__)

def memoize(f):
    """A general memoization decorator.

    Use it as follows::
        @memoize
        my_function(a, b, c):
        ...
    """
    memoize_dict = {}
    memoize_table[get_full_fn_name(f)] = memoize_dict
    def memoized_f(*args, **kw_args):
        lookup_key = (args, tuple(kw_args.iteritems()))
        if lookup_key in memoize_dict:
            return memoize_dict[lookup_key]
        else:
            memoize_dict[lookup_key] = f(*args, **kw_args)
            return memoize_dict[lookup_key]
    memoized_f._original_f = f
    return memoized_f

def get_real_fn(f):
    """Peel away any memoization layers from around a function
    and return the unmemoized function."""
    if hasattr(f, '_original_f'):
        return get_real_fn(f._original_f)
    else:
        return f

def invalidates_memoization(*functions):
    def invalid_applicator(f):
        function_names = [get_full_fn_name(get_real_fn(fn)) for fn in functions]
        def invalidating_f(*args, **kw_args):
            for function_name in function_names:
                memoize_table[function_name].clear()
            return f(*args, **kw_args)
        return invalidating_f
    return invalid_applicator
