#!/usr/bin/env python

from translate.storage import ts2 as ts
from translate.storage import test_base

class TestTSUnit(test_base.TestTranslationUnit):
    UnitClass = ts.tsunit


class TestTSfile(test_base.TestTranslationStore):
    StoreClass = ts.tsfile
    def test_basic(self):
        tsfile = ts.tsfile()
        assert tsfile.units == []
        tsfile.addsourceunit("Bla")
        assert len(tsfile.units) == 1
        newfile = ts.tsfile.parsestring(str(tsfile))
        print str(tsfile)
        assert len(newfile.units) == 1
        assert newfile.units[0].source == "Bla"
        assert newfile.findunit("Bla").source == "Bla"
        assert newfile.findunit("dit") is None
    
    def test_source(self):
        tsfile = ts.tsfile()
        tsunit = tsfile.addsourceunit("Concept")
        tsunit.source = "Term"
        newfile = ts.tsfile.parsestring(str(tsfile))
        print str(tsfile)
        assert newfile.findunit("Concept") is None
        assert newfile.findunit("Term") is not None
    
    def test_target(self):
        tsfile = ts.tsfile()
        tsunit = tsfile.addsourceunit("Concept")
        tsunit.target = "Konsep"
        newfile = ts.tsfile.parsestring(str(tsfile))
        print str(tsfile)
        assert newfile.findunit("Concept").target == "Konsep"
		
