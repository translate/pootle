# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.plugin.delegate import Getter, Provider
from pootle.core.plugin.results import GatheredList


config = Getter(providing_args=["instance"])

# search_backend
search_backend = Getter(providing_args=["instance"])
lang_mapper = Getter(providing_args=["instance"])
state = Getter()
response = Getter()

serializers = Provider(providing_args=["instance"])
deserializers = Provider(providing_args=["instance"])
subcommands = Provider()

# view.context_data
context_data = Provider(providing_args=["view", "context"])

# custom path mangling
# returns:
#   pootle_path
#   path_other: bit in between ctx_path and resource_path
#   path_extra: dict containing any parsed vars/objects
extracted_path = Getter(providing_args=["view", "instance"])

# unit.priority
unit_priority = Getter(providing_args=["instance", "stats", "user"])

# object.stats
object_stats = Provider(
    providing_args=["instance", "stats", "user"])

# object.parents
object_parents = Provider(
    providing_args=["instance", "parents"],
    result_class=GatheredList)

# child pootle_paths
pootle_paths = Provider(
    providing_args=["instance", "pootle_paths"],
    result_class=GatheredList)

# custom search filters
search_filters = Provider(
    providing_args=["search_backend", "filter_kwargs"])
