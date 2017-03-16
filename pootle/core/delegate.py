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
contributors = Getter()
display = Getter()
event_score = Provider()
formats = Getter()
format_registration = Provider()
format_classes = Provider()
format_diffs = Provider()
format_updaters = Provider()
format_syncers = Provider()
frozen = Getter()
filetype_tool = Getter()
lifecycle = Getter()
log = Getter()
stemmer = Getter()
terminology = Getter()
terminology_matcher = Getter()
tp_tool = Getter()
data_tool = Getter()
data_updater = Getter()

language_team = Getter()
review = Getter()
revision = Getter()
revision_updater = Getter()
scores = Getter()
score_updater = Getter()
site = Getter()
stopwords = Getter()
text_comparison = Getter()
panels = Provider()

serializers = Provider(providing_args=["instance"])
deserializers = Provider(providing_args=["instance"])
subcommands = Provider()
uniqueid = Getter()
unitid = Provider()
url_patterns = Provider()
wordcount = Getter()

# view.context_data
context_data = Provider(providing_args=["view", "context"])

upstream = Provider()
