#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

"""An object to represent a "search" or "navigation" over a search query, the
results of a quality check, or similar.

This is not a Django model.
"""

import bisect

from translate.tools import pogrep

from pootle_app.lib.util          import lazy_property

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


def narrow_to_search_text(total, store, translatables, search):
    if search.search_text not in (None, '') and search.search_results is None:
        # We'll get here if the user is searching for a piece of text and if no indexer
        # (such as Xapian or Lucene) is usable. First build a grepper...
        grepfilter = pogrep.GrepFilter(search.search_text, search.search_fields, ignorecase=True)
        # ...then filter the items using the grepper.
        return (item for item in translatables 
                if grepfilter.filterunit(store.units[item]))

    elif search.search_results is not None:
        mapped_indices = [total[item] for item in search.search_results[store.pootle_path]]
        return intersect(mapped_indices, translatables)
    else:
        return translatables


def narrow_to_matches(stats, translatables, search):
    if len(search.match_names) > 0:
        matches = reduce(set.__or__,
                         (set(stats[match_name])
                          for match_name in search.match_names
                          if match_name in stats),
                         set())
        return intersect(sorted(matches), translatables)
    else:
        return translatables


def search_results_to_dict(hits):
    result_dict = {}
    for doc in hits:
        filename, item = doc["pofilename"][0], int(doc["itemno"][0])
        if filename not in result_dict:
            result_dict[filename] = []
        result_dict[filename].append(item)
    for lst in result_dict.itervalues():
        lst.sort()
    return result_dict


def do_search_query(indexer, search):
    searchparts = []
    # Split the search expression into single words. Otherwise xapian and
    # lucene would interprete the whole string as an "OR" combination of
    # words instead of the desired "AND".
    for word in search.search_text.split():
        # Generate a list for the query based on the selected fields
        querylist = [(f, word) for f in search.search_fields]
        textquery = indexer.make_query(querylist, False)
        searchparts.append(textquery)
    # TODO: add other search items
    limitedquery = indexer.make_query(searchparts, True)
    return indexer.search(limitedquery, ['pofilename', 'itemno'])


class Search(object):
    def __init__(self, match_names=[], search_text=None, search_fields=None, translation_project=None):
        self.match_names     = match_names
        self.search_text     = search_text
        if search_fields is None:
            search_fields = ['source', 'target']
        self.search_fields   = search_fields
        self.translation_project = translation_project

    def _get_search_results(self):
        if self.search_text not in (None, '') and \
                self.translation_project is not None and \
                self.translation_project.has_index:
            return search_results_to_dict(do_search_query(self.translation_project.indexer, self))
        else:
            return None

    search_results = lazy_property('_search_results', _get_search_results)

    def contains_only_file_specific_criteria(self):
        return self.search_text in (None, '') and self.match_names == []

    def _all_matches(self, store, last_index, range, transform):
        if self.contains_only_file_specific_criteria():
            # This is a special shortcut that we use when we don't
            # need to narrow our search based on unit-specific
            # properties. In this case, we know that last_item is the
            # sought after item, unless of course item >= number of
            # units
            total = store.getquickstats()['total']
            if last_index < total:
                return iter([last_index])
            else:
                return iter([])
        else:
            if self.search_results is not None and \
                    store.pootle_path not in self.search_results:
                return iter([])

            stats = store.file.getcompletestats(self.translation_project.checker)
            total = stats['total']
            result = total[range[0]:range[1]]
            result = narrow_to_matches(stats, result, self)
            result = narrow_to_search_text(total, store, result, self)
            return (bisect.bisect_left(total, item) for item in transform(result))

    def next_matches(self, store, last_index):
        # stats['total'] is an array of indices into the units array
        # of a store. But we want indices of the units that we see in
        # Pootle. bisect.bisect_left of a member in stats['total']
        # gives us the index of the unit as we see it in Pootle.
        if last_index < 0:
            last_index = 0
        return self._all_matches(store, last_index, (last_index, None), lambda x: x)

    def prev_matches(self, store, last_index):
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
            stats = store.getquickstats()
            last_index = stats['total'] - 1
        return self._all_matches(store, last_index, (0, last_index + 1), lambda x: reversed(list(x)))

