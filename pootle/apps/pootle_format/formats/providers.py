# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import format_diffs, format_syncers
from pootle.core.plugin import provider

from .mozilla_lang import DiffableLangStore, LangStoreSyncer
from .po import PoStoreSyncer


@provider(format_syncers)
def register_format_syncers(**kwargs_):
    return dict(
        po=PoStoreSyncer,
        lang=LangStoreSyncer)


@provider(format_diffs)
def lang_diff_provider(**kwargs_):
    return dict(lang=DiffableLangStore)
