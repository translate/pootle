#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
# 
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import urllib
import copy

def strip_trailing_slash(path):
    """If path ends with a /, strip it and return the stripped version."""
    if len(path) > 0 and path[-1] == '/':
        return path[:-1]
    else:
        return path

def add_trailing_slash(path):
    """If path does not end with /, add it and return."""
    if len(path) > 0 and path[-1] == '/':
        return path
    else:
        return path + '/'

################################################################################

def url_split(path):
    try:
        slash_pos = strip_trailing_slash(path).rindex('/')
        return path[:slash_pos+1], path[slash_pos+1:]
    except ValueError:
        return '', path

def split_trailing_slash(p):
    if p[-1] == u'/':
        return p[:-1], p[-1]
    else:
        return p, u''

def get_relative(ref_path, abs_path):
    def get_last_agreement(ref_chain, abs_chain):
        max_pos = min(len(ref_chain), len(abs_chain))
        for i in xrange(max_pos):
            if ref_chain[i] != abs_chain[i]:
                return i
        return max_pos

    abs_path, abs_slash = split_trailing_slash(abs_path)

    ref_chain = ref_path.split('/')
    ref_chain.pop()

    abs_chain = abs_path.split('/')

    cut_pos = get_last_agreement(ref_chain, abs_chain)
    go_up = (len(ref_chain) - cut_pos) * ['..']
    go_down = abs_chain[cut_pos:]
    result = u'/'.join(go_up + go_down)
    if result == '' and abs_slash != '':
        return './'
    else:
        return result + abs_slash

class URL(object):
    def __init__(self, path, state=None):
        self.path = path
        if state is not None:
            self.state = state
        else:
            self.state = read_all_state({})

    def __str__(self):
        return self.as_relative('')

    def _get_parent(self):
        p = copy.copy(self)
        p.path, _ = url_split(self.path)
        return p

    parent = property(_get_parent)

    def child(self, child_name):
        c = copy.copy(self)
        c.path = self.path + child_name
        return c

    def _get_basename(self):
        tail, head = url_split(self.path)
        return strip_trailing_slash(head)

    basename = property(_get_basename)

    def as_relative(self, ref_path):
        def build_param_dict(state):
            result = {}
            for state_instance in state.itervalues():
                result.update(state_instance.encode())
            return result

        path = get_relative(ref_path, self.path)
        params = build_param_dict(self.state)
        if len(params) > 0:
            return u'%s?%s' % (path, urllib.urlencode(sorted(params.iteritems())))
        else:
            return path

    def as_relative_to_path_info(self, request):
        return self.as_relative(request.path_info)

    def copy_and_set(self, state_name, **kwargs):
        new_url = copy.deepcopy(self)
        for property_name, property_value in kwargs.iteritems():
            setattr(new_url.state[state_name], property_name, property_value)
        return new_url

################################################################################

class Value(object):
    default_value = None

    def __init__(self, var_name):
        self.var_name = var_name

    def _member_name(self):
        return '_' + self.var_name

    def __get__(self, obj, type=None):
        return getattr(obj, self._member_name(), self.default_value)

    def __set__(self, obj, value):
        setattr(obj, self._member_name(), value)

    def __delete__(self, obj):
        delattr(obj, self._member_name())

    def add_to_dict(self, obj, dct):
        value = self.__get__(obj)
        if value != self.default_value:
            dct[self.var_name] = self._encode(value)

    def read_from_params(self, obj, params):
        try:
            self.__set__(obj, self._decode(params[self.var_name]))
        except KeyError:
            pass

    def _decode(self, value):
        return value

    def _encode(self, value):
        return value

class GoalValue(Value):
    default_value = None

    def _decode(self, value):
        try:
            return Goal.objects.get(name=value)
        except Goal.DoesNotExist:
            return None

    def _encode(self, value):
        if value is not None:
            return value.name
        else:
            return ''

class BooleanValue(Value):
    default_value = False

    def _decode(self, value):
        if value == 'True':
            return True
        else:
            return False

    def _encode(self, value):
        if value:
            return 'True'
        else:
            return 'False'

class IntValue(Value):
    def __init__(self, var_name, default_value):
        super(IntValue, self).__init__(var_name)
        self.default_value = default_value

    def _decode(self, value):
        try:
            return int(value)
        except ValueError:
            return self.default_value

    def _encode(self, value):
        return str(value)

class ChoiceValue(Value):
    def __init__(self, var_name, choices):
        super(ChoiceValue, self).__init__(var_name)
        self.default_value = choices[0]
        self._choices = choices

    def _decode(self, value):
        if value in self._choices:
            return value
        else:
            return self.default_value

class ListValue(Value):
    default_value = []

    def _decode(self, value):
        return value.split(',')

    def _encode(self, value):
        return ','.join(str(item) for item in value)

class State(object):
    def iter_descriptors(self):
        for member in self.__class__.__dict__.itervalues():
            if isinstance(member, Value):
                yield member

    def iter_items(self):
        for member in self.iter_descriptors():
            yield member.var_name, getattr(self, member.var_name)

    def as_dict(self):
        return dict(self.iter_items())

    def __init__(self, data={}, initial={}):
        for member in self.iter_descriptors():
            member.read_from_params(self, data)
        for key, value in initial.iteritems():
            setattr(self, key, value)

    def encode(self):
        result = {}
        for member in self.iter_descriptors():
            member.add_to_dict(self, result)
        return result

class TranslateDisplayState(State):
    show_checks   = BooleanValue('show_checks')
    show_assigns  = BooleanValue('show_assings')
    editing       = BooleanValue('editing')
    view_mode     = ChoiceValue('view_mode', ('view', 'review', 'translate', 'raw'))

class SearchState(State):
    goal          = GoalValue('goal')
    match_names   = ListValue('match_names')
    assigned_to   = ListValue('assigned_to')
    search_text   = Value('search_text')
    search_fields = ListValue('search_fields')

class PositionState(State):    
    store         = Value('store')
    item          = IntValue('item', 0)

def read_all_state(data):
    return {
        "translate_display": TranslateDisplayState(data),
        "search":            SearchState(data),
        "position":          PositionState(data) }

