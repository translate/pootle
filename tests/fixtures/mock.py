#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Monkeypatching fixtures."""

from _pytest.monkeypatch import monkeypatch


# HACKISH: monkeypatching decorator here, should be cleaner to do it in a
# fixture, but pytest's `monkeypatch` decorator is function-scoped, and by
# the time it's run the decorators have already been applied to the
# functions, therefore the patching has no effect
mp = monkeypatch()
mp.setattr('django.utils.functional.cached_property', property)


class FakeJob(object):
    id = 'FAKE_JOB_ID'


mp.setattr('rq.get_current_job', lambda: FakeJob())
