# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from pootle.core.plugin.delegate import Getter, Provider


config = Getter(providing_args=["instance"])
search_backend = Getter(providing_args=["instance"])
lang_mapper = Getter(providing_args=["instance"])
state = Getter()
response = Getter()

serializers = Provider(providing_args=["instance"])
deserializers = Provider(providing_args=["instance"])
subcommands = Provider()

# view.context_data
context_data = Provider(providing_args=["view", "context"])
