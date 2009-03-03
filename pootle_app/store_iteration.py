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

from pootle_app.goals import StoreAssignment
from pootle_app.fs_models import Store, Directory, FakeSearch
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

def get_filtered_matches(get_matches, starting_store, search, last_index, depth):
    """If starting_store is not None, then we want to start iteration
    at some store in a subdirectory.

    The number of directories we have to descend before reaching the
    directory containing the store we want is len(starting_store) - 1
    (this is because the last element in starting_store is the name of
    the store that we're looking for).

    Thus, if depth < len(starting_store) - 1, we're still descending
    directories looking for the starting store. This also means that
    we want to skip past all the stores in the directories that we are
    descending (remember that our algorithm first enumerates stores
    and then directories; therefore, if we are descending directories
    we should be past stores in those directories.

    When depth == len(starting_store) - 1, we've reached the directory
    containing the store that we want. Now, we want to skip past all
    the stores which are lexicographically smaller than the store we
    want, so we issue the query
    directory.filter_child_stores(search.goal).filter(name__gte=starting_store[-1]).

    If starting_store is None, we just enumerate all the stores in the
    current directory.
    """
    if starting_store is not None:
        if depth < len(starting_store) - 1:
            return []
        else:
            return get_matches(search, starting_store[-1], last_index)
    else:
        return get_matches(search)

def get_next_subdirs(directory, starting_store, depth):
    """If starting_store is not None, then we want to start iteration
    at some store in a subdirectory.

    To see how this works, suppose we want to start iteration at a
    store at the path ['foo', 'bar', 'baz', 'quux.po']. If depth == 2,
    then we have already descended to the directory 'foo/bar' (foo is
    at depth 0 and bar is at depth 1). Thus, starting_store[depth] ==
    'baz' where depth == 2.  We definitely want to skip everything
    before 'baz' in the directory 'foo/bar', so that's why we issue
    the query
    directory.child_dirs.filter(name__gte=starting_store[depth]). This
    works, because subdirectories are ordered lexicographically (see
    the model definition of Directory).

    On the other hand, if starting_store is None, then we just want to
    enumerate all subdirectories.
    """
    if starting_store is not None:
        return directory.child_dirs.filter(name__gte=starting_store[depth])
    else:
        return directory.child_dirs.all()

def iter_next_matches_recur(directory, starting_store, last_index, search, depth=0):
    """Iterate over all the stores contained in the directory
    'directory'. For each directory, all the stores are first iterated
    in lexicographical ordering, and then the subdirectories are
    iterated in lexicographical ordering.

    @param directory: A Directory object giving the root relative to
                      which we want to iterate

    @param starting_store: None or a string containing a list of path
                           components which are relative to the
                           directory specified by 'directory' (for
                           example ['a', 'b', 'c.po'])

    @param search: A search object which is used to filter out stores
                   based on the user's search criteria. This object
                   should contain a 'goal' member (to allow filtering
                   based on goals) and a method called 'matches' which
                   takes a store and returns a boolean value
                   specifying whether it should be included in the
                   iteration or not.

    @param depth: Keeps track of the recursion depth. This is used to
                  find the component in 'starting_store' (if
                  'starting_store' is not None) which corresponds to the
                  current directory being considered.
    """
    for store, match_index in get_filtered_matches(directory.next_matches, starting_store, search, last_index, depth):
        yield store, match_index
        # If there are any files at all the enumerate, then we've
        # found what we were looking for with starting_store. Therefore,
        # nuke its value now, so that we will enumerate full
        # subdirectories from now on.
        starting_store = None
        last_index = 0

    for subdirectory in get_next_subdirs(directory, starting_store, depth):
        for store, match_index in iter_next_matches_recur(subdirectory, starting_store, last_index, search, depth + 1):
            yield store, match_index
        # After considering our first subdirectory, we should have
        # found what we were looking for with starting_store. Therefore,
        # nuke its value now, so that we will enumerate full
        # subdirectories from now on.
        starting_store = None
        last_index = 0

def iter_next_matches_store(path_obj, last_index=0, search=FakeSearch(None)):
    for match in search.next_matches(path_obj, last_index):
        yield path_obj, match

def iter_next_matches(path_obj, starting_store=None, last_index=0, search=FakeSearch(None)):
    if path_obj.is_dir:
        return iter_next_matches_recur(path_obj, get_relative_components(path_obj, starting_store), last_index, search)
    else:
        return iter_next_matches_store(path_obj, last_index, search)

################################################################################

def get_prev_subdirs(directory, starting_store, depth):
    "See get_next_subdirs"
    if starting_store is not None:
        return directory.child_dirs.filter(name__lte=starting_store[depth]).order_by('-name')
    else:
        return directory.child_dirs.all().order_by('-name')

def iter_prev_matches_recur(directory, starting_store, last_index, search, depth=0):
    "See iter_next_matches_recur"
    for subdirectory in get_prev_subdirs(directory, starting_store, depth):
        for store, match_index in iter_prev_matches_recur(subdirectory, starting_store, last_index, search, depth + 1):
            yield store, match_index
        starting_store = None
        last_index = 0

    for store, match_index in get_filtered_matches(directory.prev_matches, starting_store, search, last_index, depth):
        yield store, match_index
        starting_store = None
        last_index = 0

def iter_prev_matches_store(path_obj, last_index=0, search=FakeSearch(None)):
    for match in search.prev_matches(path_obj, last_index):
        yield path_obj, match

def iter_prev_matches(directory, starting_store=None, last_index=-1, search=FakeSearch(None)):
    "See iter_next_matches"
    if path_obj.is_dir:
        return iter_prev_matches_recur(path_obj, get_relative_components(path_obj, starting_store), last_index, search)
    else:
        return iter_prev_matches_store(path_obj, last_index, search)

################################################################################

def get_filtered_stores(directory, starting_store, search, depth):
    if starting_store is not None:
        if depth < len(starting_store) - 1:
            return Directory.objects.none()
        else:
            return directory.filter_stores(search, starting_store[-1]).all()
    else:
        return directory.filter_stores(search).all()

def iter_stores_recur(directory, starting_store, search, depth=0):
    for store in get_filtered_stores(directory, starting_store, search, depth):
        yield store
        # If there are any files at all the enumerate, then we've
        # found what we were looking for with starting_store. Therefore,
        # nuke its value now, so that we will enumerate full
        # subdirectories from now on.
        starting_store = None

    for subdirectory in get_next_subdirs(directory, starting_store, depth):
        for store in iter_stores_recur(subdirectory, starting_store, search, depth + 1):
            yield store
        # After considering our first subdirectory, we should have
        # found what we were looking for with starting_store. Therefore,
        # nuke its value now, so that we will enumerate full
        # subdirectories from now on.
        starting_store = None

def iter_stores(directory, starting_store=None, search=FakeSearch(None)):
    return iter_stores_recur(directory, get_relative_components(directory, starting_store), search)

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

def iter_indexed_stores(directory, starting_store, last_index, search):
    stores = dict((store.pootle_path, store) for store, index in iter_stores(directory, starting_store, -1, FakeSearch(search.goal)))
    result_dict = compute_index_result(search, stores)
    for store_path in sorted(stores):
        match_index = search.matches(stores[store_path], last_index, result_dict[store_path])
        if match_index > -1:
            yield store_path, match_index
        last_index = -1

################################################################################
