#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2006 Zuza Software Foundation
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

from translate.tools import pogrep
from translate.filters import checks

from pootle_app.goals import StoreAssignment
from pootle_app.fs_models import Store, Directory, Search
from pootle_app import url_manip

def member(sorted_set, element):
    """Check whether element appears in sorted_set."""
    pos = bisect.bisect_left(sorted_set, element)
    if pos < len(sorted_set):
        return sorted_set[pos] == element
    else:
        return False

def intersect(set_a, set_b):
    """Find the intersection of the sorted sets set_a and set_b."""
    # If both set_a and set_b have elements
    if len(set_b) != 0 and len(set_a) != 0:
        # Find the position of the element in set_a that is at least
        # as large as the minimum element in set_b.
        start_a = bisect.bisect_left(set_a, set_b[0])
        # For each element in set_a...
        for element in set_a[start_a:]:
            # ...which is also in set_b...
            if member(set_b, element):
                yield element

################################################################################

def get_relative_components(directory, starting_store):
    if starting_store is not None:
        return url_manip.get_relative(directory.pootle_path, starting_store).split('/')
    else:
        return None

################################################################################

BLOCK_SIZE = 10

def do_query(query, next_matches, last_index):
    i = 0
    # Read BLOCK_SIZE Stores from the database (query[x:y] creates a
    # ranged database query)...
    result = query[i:i+BLOCK_SIZE]
    while len(result) > 0:
        # For each of the just-read BLOCK_SIZE Stores...
        for store in result:
            try:
                # See whether we have a match
                return store, next_matches(store, last_index).next()
            except StopIteration:
                pass
            # If we get here, then there were no more matches in the
            # previous store. Thus, for the next store we need to
            # start at the first index.
            last_index = -1

        # Now we want to move on by BLOCK_SIZE Stores to the next
        # Stores.
        i += BLOCK_SIZE
        # Build a range query to get our next set of Stores
        result = query[i:i+BLOCK_SIZE]
    raise StopIteration()

def get_next_match(path_obj, starting_store=None, last_index=-1, search=Search()):
    if path_obj.is_dir:
        query = Store.objects.filter(pootle_path__startswith=path_obj.pootle_path).order_by('pootle_path')
        if starting_store is not None:
            query = query.filter(pootle_path__gte=starting_store)
        if search.goal is not None:
            query = query.filter(goals=search.goal)
        return do_query(query, search.next_matches, last_index)
    else:
        return path_obj, search.next_matches(path_obj, last_index).next()

def get_prev_match(path_obj, starting_store=None, last_index=-1, search=Search()):
    if path_obj.is_dir:
        query = Store.objects.filter(pootle_path__startswith=path_obj.pootle_path).order_by('-pootle_path')
        if starting_store is not None:
            query = query.filter(pootle_path__lte=starting_store)
        if search.goal is not None:
            query = query.filter(goals=search.goal)
        return do_query(query, search.prev_matches, last_index)
    else:
        return path_obj, search.next_matches(path_obj, last_index).next()

################################################################################

def iter_stores(directory, search=Search()):
    if search.goal is None:
        return Store.objects.filter(pootle_path__startswith=directory.pootle_path).order_by('pootle_path')
    else:
        return Store.objects.filter(pootle_path__startswith=directory.pootle_path, goals=search.goal)

################################################################################

def hits_to_dict(hits):
    result_dict = {}
    for hit in hits:
        key = hit['pofilename'][0]
        if key not in result_dict:
            result_dict[key] = []
        result_dict[key].append(int(hit['itemno'][0]))
    for key, items in result_dict.iteritems():
        result_dict[key] = sorted(items)
    return result_dict

def compute_index_result(search, stores):
    searchparts = []
    # Split the search expression into single words. Otherwise xapian and
    # lucene would interprete the whole string as an "OR" combination of
    # words instead of the desired "AND".
    for word in search.search_text.split():
        # Generate a list for the query based on the selected fields
        querylist = [(f, word) for f in search.search_fields]
        textquery = search.indexer.make_query(querylist, False)
        searchparts.append(textquery)
    if stores:
        #for store in iter_stores(directory, starting_store, 
        filequery = indexer.make_query([("pofilename", store) for store in stores], False)
        searchparts.append(filequery)
    # TODO: add other search items
    limitedquery = search.indexer.make_query(searchparts, True)
    return hits_to_dict(search.indexer.search(limitedquery, ['pofilename', 'itemno']))


################################################################################
