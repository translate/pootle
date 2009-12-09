#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import factory
from translate.storage import xliff
from translate.filters import pofilter
from translate.filters import checks
from translate.misc import wStringIO

class BaseTestFilter(object):
    """Base class for filter tests."""

    filename = ""

    def parse_text(self, filetext):
        """helper that parses xliff file content without requiring files"""
        dummyfile = wStringIO.StringIO(filetext)
        dummyfile.name = self.filename
        store = factory.getobject(dummyfile)
        return store

    def filter(self, translationstore, checkerconfig=None, cmdlineoptions=None):
        """Helper that passes a translations store through a filter, and returns the resulting store."""
        if cmdlineoptions is None:
            cmdlineoptions = []
        options, args = pofilter.cmdlineparser().parse_args([self.filename] + cmdlineoptions)
        checkerclasses = [checks.StandardChecker, checks.StandardUnitChecker]
        if checkerconfig is None:
            checkerconfig = checks.CheckerConfig()
        checkfilter = pofilter.pocheckfilter(options, checkerclasses, checkerconfig)
        tofile = checkfilter.filterfile(translationstore)
        return tofile

    def test_simplepass(self):
        """checks that an obviously correct string passes"""
        filter_result = self.filter(self.translationstore)
        assert len(filter_result.units) == 0

    def test_simplefail(self):
        """checks that an obviously wrong string fails"""
        self.unit.target = "REST"
        filter_result = self.filter(self.translationstore)
        assert filter_result.units[0].geterrors().has_key('startcaps')

    def test_variables_across_lines(self):
        """Test that variables can span lines and still fail/pass"""
        self.unit.source = '"At &timeBombURL."\n"label;."'
        self.unit.target = '"Tydens &tydBombURL."\n"etiket;."'
        filter_result = self.filter(self.translationstore)
        assert len(filter_result.units) == 0

    def test_ignore_if_already_marked(self):
        """check that we don't add another failing marker if the message is already marked as failed"""
        self.unit.target = ''
        filter_result = self.filter(self.translationstore, cmdlineoptions=["--test=untranslated"])
        errors = filter_result.units[0].geterrors()
        assert len(errors) == 1
        assert errors.has_key('untranslated')

        # Run a filter test on the result, to check that it doesn't mark the same error twice.
        filter_result2 = self.filter(filter_result, cmdlineoptions=["--test=untranslated"])
        errors = filter_result2.units[0].geterrors()
        assert len(errors) == 1
        assert errors.has_key('untranslated')

    def test_non_existant_check(self):
        """check that we report an error if a user tries to run a non-existant test"""
        filter_result = self.filter(self.translationstore, cmdlineoptions=["-t nonexistant"])
        # TODO Not sure how to check for the stderror result of: warning: could not find filter  nonexistant
        assert len(filter_result.units) == 0

    def test_list_all_tests(self):
        """lists all available tests"""
        filter_result = self.filter(self.translationstore, cmdlineoptions=["-l"])
        # TODO again not sure how to check the stderror output
        assert len(filter_result.units) == 0

    def test_test_against_fuzzy(self):
        """test whether to run tests against fuzzy translations"""
        self.unit.markfuzzy()

        filter_result = self.filter(self.translationstore, cmdlineoptions=["--fuzzy"])
        assert filter_result.units[0].geterrors().has_key('isfuzzy')

        filter_result = self.filter(self.translationstore, cmdlineoptions=["--nofuzzy"])
        assert len(filter_result.units) == 0

        # Re-initialize the translation store object in order to get an unfuzzy unit
	# with no filter notes.
        self.setup_method(self)

        filter_result = self.filter(self.translationstore, cmdlineoptions=["--fuzzy"])
        assert len(filter_result.units) == 0

        filter_result = self.filter(self.translationstore, cmdlineoptions=["--nofuzzy"])
        assert len(filter_result.units) == 0

    def test_test_against_review(self):
        """test whether to run tests against translations marked for review"""
        self.unit.markreviewneeded()
        filter_result = self.filter(self.translationstore, cmdlineoptions=["--review"])
        assert filter_result.units[0].isreview()

        filter_result = self.filter(self.translationstore, cmdlineoptions=["--noreview"])
        assert len(filter_result.units) == 0

        # Re-initialize the translation store object.
        self.setup_method(self)

        filter_result = self.filter(self.translationstore, cmdlineoptions=["--review"])
        assert len(filter_result.units) == 0
        filter_result = self.filter(self.translationstore, cmdlineoptions=["--noreview"])
        assert len(filter_result.units) == 0

    def test_isfuzzy(self):
        """tests the extraction of items marked fuzzy"""
        self.unit.markfuzzy()

        filter_result = self.filter(self.translationstore, cmdlineoptions=["--test=isfuzzy"])
        assert filter_result.units[0].geterrors().has_key('isfuzzy')

        self.unit.markfuzzy(False)
        filter_result = self.filter(self.translationstore, cmdlineoptions=["--test=isfuzzy"])
        assert len(filter_result.units) == 0

    def test_isreview(self):
        """tests the extraction of items marked review"""
        filter_result = self.filter(self.translationstore, cmdlineoptions=["--test=isreview"])
        assert len(filter_result.units) == 0

        self.unit.markreviewneeded()
        filter_result = self.filter(self.translationstore, cmdlineoptions=["--test=isreview"])
        assert filter_result.units[0].isreview()

    def test_notes(self):
        """tests the optional adding of notes"""
        # let's make sure we trigger the 'long' and/or 'doubleword' test
        self.unit.target = u"asdf asdf asdf asdf asdf asdf asdf"
        filter_result = self.filter(self.translationstore)
        assert len(filter_result.units) == 1
        assert filter_result.units[0].geterrors()

        # now we remove the existing error. self.unit is changed since we copy
        # units - very naughty
        if isinstance(self.unit, xliff.xliffunit):
            self.unit.removenotes(origin='pofilter')
        else:
            self.unit.removenotes()
        filter_result = self.filter(self.translationstore, cmdlineoptions=["--nonotes"])
        assert len(filter_result.units) == 1
        assert len(filter_result.units[0].geterrors()) == 0

    def test_unicode(self):
        """tests that we can handle UTF-8 encoded characters when there is no known header specified encoding"""
        self.unit.source = u'Bézier curve'
        self.unit.target = u'Bézier-kurwe'
        filter_result = self.filter(self.translationstore)
        assert len(filter_result.units) == 0

    def test_preconditions(self):
        """tests that the preconditions work correctly"""
        self.unit.source = "File"
        self.unit.target = ""
        filter_result= self.filter(self.translationstore)
        # We should only get one error (untranslated), and nothing else
        assert len(filter_result.units) == 1
        unit = filter_result.units[0]
        assert len(unit.geterrors()) == 1

class TestPOFilter(BaseTestFilter):
    """Test class for po-specific tests."""
    filetext = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
    filename = 'test.po'

    def setup_method(self, method):
        self.translationstore = self.parse_text(self.filetext)
        self.unit = self.translationstore.units[0]

    def test_msgid_comments(self):
        """Tests that msgid comments don't feature anywhere."""
        posource = 'msgid "_: Capital.  ACRONYMN. (msgid) comment 3. %d Extra sentence.\\n"\n"cow"\nmsgstr "koei"\n'
        pofile = self.parse_text(posource)
        filter_result = self.filter(pofile)
        if len(filter_result.units):
            print filter_result.units[0]
        assert len(filter_result.units) == 0

class TestXliffFilter(BaseTestFilter):
    """Test class for xliff-specific tests."""
    filetext = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
<file original='NoName' source-language="en" datatype="plaintext">
  <body>
    <trans-unit approved="yes">
      <source>test</source>
      <target>rest</target>
    </trans-unit>
  </body>
</file>
</xliff>'''
    filename = "test.xlf"

    def set_store_review(review=True):
        self.filetext = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
<file datatype="po" original="example.po" source-language="en-US">
  <body>
    <trans-unit approved="yes">
      <source>test</source>
      <target>rest</target>
    </trans-unit>
  </body>
</file>
</xliff>'''

        self.translationstore = self.parse_text(self.filetext)
        self.unit = self.translationstore.units[0]

    def setup_method(self, method):
        self.translationstore = self.parse_text(self.filetext)
        self.unit = self.translationstore.units[0]

class TestTMXFilter(BaseTestFilter):
    """Test class for TMX-specific tests."""
    filetext = '''<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx version="1.4">
  <header creationtool="Translate Toolkit - po2tmx" creationtoolversion="1.1.1rc1" segtype="sentence" o-tmf="UTF-8" adminlang="en" srclang="en
" datatype="PlainText"/>
  <body>
    <tu>
      <tuv xml:lang="en">
        <seg>test</seg>
      </tuv>
      <tuv xml:lang="af">
        <seg>rest</seg>
      </tuv>
    </tu>
  </body>
</tmx>'''
    filename = "test.tmx"

    def setup_method(self, method):
        self.translationstore = self.parse_text(self.filetext)
        self.unit = self.translationstore.units[0]

    def test_test_against_fuzzy(self):
        """TMX doesn't support fuzzy"""
        pass

    def test_test_against_review(self):
        """TMX doesn't support review"""
        pass

    def test_isfuzzy(self):
        """TMX doesn't support fuzzy"""
        pass

    def test_isreview(self):
        """TMX doesn't support review"""
        pass
