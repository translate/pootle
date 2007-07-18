#!/usr/bin/env python

from Pootle import pootlefile
from Pootle import pootle
from Pootle import projects
from translate.storage import po
from translate.storage import test_po
from translate.filters import pofilter
from translate.misc import wStringIO

import os

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

        checkerclasses = [projects.checks.StandardChecker, projects.checks.StandardUnitChecker]
        stdchecker = projects.pofilter.POTeeChecker(checkerclasses=checkerclasses, errorhandler=filtererrorhandler)
        dummyproject = projects.DummyStatsProject(self.rundir, stdchecker, "unittest_project", "xx")

        pofile = pootlefile.pootlefile(dummyproject, "test.po", generatestats=False)
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
        unit = pofile.units[0]
        assert unit.getlocations() == ["test.c"]
        assert unit.source == "test"
        assert unit.target == "rest"

    def test_classify(self):
        """Test basic classification"""
        posource = 'msgid "test"\nmsgstr ""\n'
        pofile = self.poparse(posource)
        pofile.project.checker = pofilter.POTeeChecker()
        unit = pofile.units[0]
        classify = pofile.statistics.classifyunit
        classes = classify(unit)
        assert 'blank' in classes
        unit.target = "Gom"
        classes = classify(unit)
        assert 'translated' in classes
        assert 'blank' not in classes
        unit.markfuzzy()
        classes = classify(unit)
        assert 'fuzzy' in classes

    def test_classifyunits(self):
        "Tests basic use of classifyunits."
        posource = r'''#: test.c
msgid "test"
msgstr "rest"

#, fuzzy
msgid "tabel"
msgstr "tafel"

msgid "chair"
msgstr ""'''
        pofile = self.poparse(posource)
        pofile.transunits = [poel for poel in pofile.units if not (poel.isheader() or poel.isblank())]
        pofile.statistics.classifyunits()
        classify = pofile.statistics.classify
        print classify
        for i in pofile.units:
            print str(i)
        assert classify['fuzzy'] == [1]
        assert classify['blank'] == [2]
        assert len(classify['total']) == 3

    def test_updateunit(self):
        """Test the updateunit() method."""
        posource = '#: test.c\nmsgid "upd"\nmsgstr "update"\n'
        testdir = os.path.join(self.testdir, 'unittest_project', 'xx')
        filename = self.filename
        filepath = os.path.join(testdir, filename)
        file(filepath, 'w').write(posource)
        dummy_project = projects.DummyProject(podir=testdir)
        pofile = pootlefile.pootlefile(project=dummy_project, pofilename=filename)

        newvalues = {}
        pofile.updateunit(0, newvalues, None, None)
        translation_unit = pofile.units[1]
        assert translation_unit.target == "update"
        assert not translation_unit.isfuzzy()
        assert str(translation_unit) == posource

        newvalues = {"target": "opdateer"}
        pofile.updateunit(0, newvalues, None, None)
        assert translation_unit.target == "opdateer"
        assert not translation_unit.isfuzzy()
        expected_posource = '#: test.c\nmsgid "upd"\nmsgstr "opdateer"\n'
        assert str(translation_unit) == expected_posource

        newvalues = {"fuzzy": True}
        pofile.updateunit(0, newvalues, None, None)
        assert translation_unit.target == "opdateer"
        assert translation_unit.isfuzzy()
        expected_posource = '#: test.c\n#, fuzzy\nmsgid "upd"\nmsgstr "opdateer"\n'
        assert str(translation_unit) == expected_posource

        newvalues = {"translator_comments": "Test comment."}
        pofile.updateunit(0, newvalues, None, None)
        assert translation_unit.target == "opdateer"
        assert translation_unit.isfuzzy()
        expected_posource = '# Test comment.\n#: test.c\n#, fuzzy\nmsgid "upd"\nmsgstr "opdateer"\n'
        assert str(translation_unit) == expected_posource
