#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import Signal


changed = Signal(
    providing_args=["instance", "updates"],
    use_caching=True)
create = Signal(
    providing_args=["instance", "objects"],
    use_caching=True)
delete = Signal(
    providing_args=["instance", "objects"],
    use_caching=True)
update = Signal(
    providing_args=["instance", "objects"],
    use_caching=True)
update_checks = Signal(
    providing_args=["instance", "keep_false_positives"],
    use_caching=True)
update_data = Signal(providing_args=["instance"], use_caching=True)
update_revisions = Signal(providing_args=["instance"], use_caching=True)
filetypes_changed = Signal(
    providing_args=["instance", "filetype"],
    use_caching=True)
update_scores = Signal(
    providing_args=["instance", "users"],
    use_caching=True)
toggle = Signal(
    providing_args=["instance", "false_positive"],
    use_caching=True)
