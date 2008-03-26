#!/usr/bin/env python

from translate.storage import odf
from translate.storage import test_monolingual
from translate.misc import wStringIO

class TestODFUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = odf.ODFUnit

#    def test_markreview(self):
#        assert test.raises(NotImplementedError, self.unit.markreviewneeded)

class TestODFFile(test_monolingual.TestMonolingualStore):
    StoreClass = odf.ODFFile
    def odfparse(self, odfsource):
        """helper that parses odf source without requiring files"""
        dummyfile = wStringIO.StringIO(odfsource)
        odffile = self.StoreClass(dummyfile)
        return odffile

    def odfregen(self, odfsource):
        """helper that converts odf source to odffile object and back"""
        return str(self.odfparse(odfsource))

#    def test_simpleblock(self):
#        """checks that a simple odf block is parsed correctly"""
#        odfsource = 'bananas for sale'
#        odffile = self.odfparse(odfsource)
#        assert len(odffile.units) == 1
#        assert odffile.units[0].source == odfsource
#        assert self.odfregen(odfsource) == odfsource
#
#    def test_multipleblocks(self):
#        """ check that multiple blocks are parsed correctly"""
#        odfsource = '''One\nOne\n\nTwo\n---\n\nThree'''
#        odffile = self.odfparse(odfsource)
#        assert len(odffile.units) == 3
#        print odfsource
#        print str(odffile)
#        print "*%s*" % odffile.units[0]
#        assert str(odffile) == odfsource
#        assert self.odfregen(odfsource) == odfsource
