#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
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

import bisect

from django.db                import models
from django.utils.translation import ugettext_lazy as _

from pootle_app.models.goals import StoreAssignment

from Pootle.pootlefile import with_pootle_file

def member(sorted_set, element):
    """Check whether element appears in sorted_set."""
    pos = bisect.bisect_left(sorted_set, element)
    if pos < len(sorted_set):
        return sorted_set[pos] == element
    else:
        return False

def as_seq_with_len(seq):
    if not hasattr(seq.__class__, '__len__'):
        return list(seq)
    else:
        return seq

def intersect(set_a, set_b):
    """Find the intersection of the sorted sets set_a and set_b."""
    # If both set_a and set_b have elements
    set_a = as_seq_with_len(set_a)
    set_b = as_seq_with_len(set_b)
    if len(set_b) != 0 and len(set_a) != 0:
        # Find the position of the element in set_a that is at least
        # as large as the minimum element in set_b.
        start_a = bisect.bisect_left(set_a, set_b[0])
        # For each element in set_a...
        for element in set_a[start_a:]:
            # ...which is also in set_b...
            if member(set_b, element):
                yield element

def narrow_to_last_item_range(translatables, last_index):
    return translatables[last_index + 1:]

def narrow_to_index_subset(translatables, index_subset):
    if index_subset is not None:
        return intersect(index_subset, translatables)
    else:
        return translatables

def narrow_to_search_text(store, translatables, search):
    def do_slow_search(pootle_file):
        # We'll get here if the user is searching for a piece of text and if no indexer
        # (such as Xapian or Lucene) is usable. First build a grepper...
        grepfilter = pogrep.GrepFilter(search.searchtext, search.searchfields, ignorecase=True)
        # ...then filter the items using the grepper.
        return (index for index in translatables 
                        if grepfilter.filterunit(pootle_file.items[item]))

    if search.search_text is not None:
        return with_pootle_file(search.translation_project, store.abs_real_path, do_slow_search)
    else:
        return translatables

def narrow_to_assigns(store, translatables, search):
    if len(search.assigned_to) > 0:
        assignments = StoreAssignment.objects.filter(assignment__in=search.assigned_to, store=store)
        assigned_indices = reduce(set.__or__, [assignment.unit_assignments for assignment in assignments], set())
        return intersect(sorted(assigned_indices), translatables)    
    else:
        return translatables

def narrow_to_matches(stats, translatables, search):
    if len(search.match_names) > 0:
        matches = reduce(set.__or__,
                         (set(stats[match_name]) for match_name in search.match_names if match_name in stats),
                         set())
        return intersect(sorted(matches), translatables)
    else:
        return translatables

class Search(object):
    @classmethod
    def from_request(cls, request):
        def get_list(request, name):
            try:
                return request.GET[name].split(',')
            except KeyError:
                return []

        kwargs = {}
        if 'goal' in request.GET:
            kwargs['goal'] = Goal.objects.get(name=request.GET['goal'])
        kwargs['match_names']         = get_list(request, 'match_names')
        kwargs['assigned_to']         = get_list(request, 'assigned_to')
        kwargs['search_text']         = request.GET.get('search_text', None)
        kwargs['search_fields']       = get_list(request, 'search_fields')
        kwargs['translation_project'] = request.translation_project
        return cls(**kwargs)

    def __init__(self, goal=None, match_names=[],
                 assigned_to=[], search_text=None, search_fields=None,
                 translation_project=None):
        self.goal            = goal
        self.match_names     = match_names
        self.assigned_to     = assigned_to
        self.search_text     = search_text
        self.search_fields   = search_fields
        if search_fields is None: # TDB: This is wrong
            search_fiels = ['source', 'target']
        self.translation_project = translation_project

    def contains_only_file_specific_criteria(self):
        return self.search_text is None  and \
            self.match_names == [] and \
            self.assigned_to == []

    def _get_index_results():
        if self._index_results is None:
            self._index_results = compute_index_result(self)
        return self._index_results

    def _all_matches(self, store, stats, range, index_subset):
        return \
            narrow_to_search_text( # Reduce to the search results. This is called when 
                store,             # we don't use a search indexer
                narrow_to_assigns( # Reduce to everything matching the current assingment
                    store,
                    narrow_to_matches( # Reduce to everything matching names like xmltags
                        stats,
                        narrow_to_index_subset( 
                            stats['total'][range[0]:range[1]],
                            index_subset),
                        self),
                    self),
                self)

    def next_matches(self, store, last_index, index_subset=None):
        # stats['total'] is an array of indices into the units array
        # of a store. But we want indices of the units that we see in
        # Pootle. bisect.bisect_left of a member in stats['total']
        # gives us the index of the unit as we see it in Pootle.
        if last_index < 0:
            last_index = 0
        if self.contains_only_file_specific_criteria():
            # This is a special shortcut that we use when we don't
            # need to narrow our search based on unit-specific
            # properties. In this case, we know that last_item is the
            # sought after item, unless of course item >= number of
            # units
            stats = store.get_stats_totals(self.translation_project.checker)
            if last_index < stats['total']:
                return iter([last_index])
            else:
                return iter([])
        else:
            stats = store.get_property_stats(self.translation_project.checker)
            matches = list(self._all_matches(store, stats, (last_index, None), index_subset))
            return (bisect.bisect_left(stats['total'], item) for item in matches)

    def prev_matches(self, store, last_index, index_subset=None):
        if last_index < 0:
            # last_index = -1 means that last_index is
            # unspecified. Normally this means that we want to start
            # searching at the start of stores. But in reverse
            # iteration mode, we view len(stats['total']) as
            # equivalent to the position of -1. This is because we
            # consider all elements in stats['total'] in the range [0,
            # last_index]. Thus, if we don't yet have a valid index
            # into the file, we want to include the very last element
            # of stats['total'] as well when searching. Thus
            # [0:len(stats['total'])] gives us what we need.
            last_index = len(stats['total']) - 1
        if self.contains_only_file_specific_criteria():
            # This is a special shortcut that we use when we don't
            # need to narrow our search based on unit-specific
            # properties. In this case, we know that last_item is the
            # sought after item.
            # units
            return iter([last_index])
        else:
            stats = store.get_property_stats(self.translation_project.checker)
            matches = list(self._all_matches(store, stats, (0, last_index + 1), index_subset))
            return (bisect.bisect_left(stats['total'], item) for item in reversed(matches))

def search_from_state(translation_project, search_state):
    return Search(translation_project=translation_project, **search_state.as_dict())
