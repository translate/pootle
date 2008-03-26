#!/usr/bin/env python

from translate.storage import test_base
from translate.storage import mo

class TestMOUnit(test_base.TestTranslationUnit):
    UnitClass = mo.mounit

class TestMOFile(test_base.TestTranslationStore):
    StoreClass = mo.mofile
