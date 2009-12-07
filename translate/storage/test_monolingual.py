#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
# These test classes should be used as super class of test classes for the
# classes that doesn't support the target property

from translate.storage import test_base
from translate.storage import base

class TestMonolingualUnit(test_base.TestTranslationUnit):
    UnitClass = base.TranslationUnit

    def test_target(self):
        pass

    def test_rich_get(self):
        pass

    def test_rich_set(self):
        pass


class TestMonolingualStore(test_base.TestTranslationStore):
    StoreClass = base.TranslationStore

    def test_translate(self):
        pass

    def test_markup(self):
        pass

    def test_nonascii(self):
        pass

