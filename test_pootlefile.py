#!/usr/bin/env python

from Pootle import pootlefile
from Pootle import pootle
from Pootle import projects
from translate.storage import po
from translate.storage import test_po
from translate.filters import pofilter
from translate.misc import wStringIO

import os

class TestPootleUnit(test_po.TestPOUnit):
    UnitClass = pootlefile.pootleelement
    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(posource)
        pofile = po.pofile(dummyfile, unitclass=self.UnitClass)
        return pofile

    def test_classify(self):
        """Test basic classification"""
        dummy_checker = pofilter.POTeeChecker()
        unit = self.UnitClass("Glue")
        classes = unit.classify(dummy_checker)
        assert 'blank' in classes
        unit.target = "Gom"
        classes = unit.classify(dummy_checker)
        assert 'translated' in classes
        assert 'blank' not in classes
        unit.markfuzzy()
        classes = unit.classify(dummy_checker)
        assert 'fuzzy' in classes

class TestPootleFile(test_po.TestPO):
    class pootletestfile(pootlefile.pootlefile):
        def __init__(self):
            """wrapper constructor for pootlefile that uses temporary filename"""
            project = projects.DummyProject(self.testdir)
            return pootlefile.pootlefile.__init__(self, project, self.pofilename)

    StoreClass = pootletestfile

    def setup_method(self, method):
        """creates a clean test directory for the given method"""
        self.testdir = "%s_%s" % (self.__class__.__name__, method.__name__)
        self.filename = "%s_%s.po" % (self.__class__.__name__, method.__name__)
        self.pootletestfile.testdir = self.testdir
        self.pootletestfile.pofilename = self.filename
        self.cleardir()
        os.mkdir(self.testdir)
        self.rundir = os.path.abspath(os.getcwd())
        #potree.podirectory = self.testdir
        os.mkdir(os.path.join(self.testdir, 'unittest_project'))
        os.mkdir(os.path.join(self.testdir, 'unittest_project', 'xx'))
        posource = r'''#: test.c
msgid "test"
msgstr "rest"

#, fuzzy
msgid "tabel"
msgstr "tafel"

msgid "chair"
msgstr ""'''
        file(os.path.join(self.testdir, 'unittest_project', 'xx', 'test.po'), 'w').write(posource)

    def teardown_method(self, method):
        """removes the test directory for the given method"""
        os.chdir(self.rundir)
        self.cleardir()

    def cleardir(self):
        """removes the test directory"""
        if os.path.exists(self.testdir):
            for dirpath, subdirs, filenames in os.walk(self.testdir, topdown=False):
                for name in filenames:
                    os.remove(os.path.join(dirpath, name))
                for name in subdirs:
                    os.rmdir(os.path.join(dirpath, name))
        if os.path.exists(self.testdir): os.rmdir(self.testdir)
        assert not os.path.exists(self.testdir)

    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        def filtererrorhandler(functionname, str1, str2, e):
            print "error in filter %s: %r, %r, %s" % (functionname, str1, str2, e)
            return False

        checkerclasses = [projects.checks.StandardChecker, projects.pofilter.StandardPOChecker]
        stdchecker = projects.pofilter.POTeeChecker(checkerclasses=checkerclasses, errorhandler=filtererrorhandler)
        dummyproject = projects.DummyStatsProject(self.rundir, stdchecker, "unittest_project", "xx")

        pofile = pootlefile.pootlefile(dummyproject, "test.po", stats=False)
        pofile.parse(posource)
        return pofile

    def poregen(self, posource):
        """helper that converts po source to pofile object and back"""
        return str(self.poparse(posource))

    def test_simpleentry(self):
        """checks that a simple po entry is parsed correctly"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 1
        thepo = pofile.units[0]
        assert thepo.getlocations() == ["test.c"]
        assert thepo.source == "test"
        assert thepo.target == "rest"

    def test_classifyelements(self):
        "Tests basic use of classifyelements."
        posource = r'''#: test.c
msgid "test"
msgstr "rest"

#, fuzzy
msgid "tabel"
msgstr "tafel"

msgid "chair"
msgstr ""'''
        pofile = self.poparse(posource)
        pofile.transelements = [poel for poel in pofile.units if not (poel.isheader() or poel.isblank())]
        pofile.classifyelements()
        print pofile.classify
        for i in pofile.units:
            print str(i)
        assert pofile.classify['fuzzy'] == [1]
        assert pofile.classify['blank'] == [2]
        assert len(pofile.classify['total']) == 3

