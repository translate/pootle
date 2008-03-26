#!/usr/bin/env python

from translate.storage import dtd
from translate.storage import test_monolingual
from translate.misc import wStringIO

def test_roundtrip_quoting():
    specials = ['Fish & chips', 'five < six', 'six > five',
                'Use &nbsp;', 'Use &amp;nbsp;' 
                'A "solution"', "skop 'n bal", '"""', "'''",
                '\n', '\t', '\r',
                'Escape at end \\',
                '\\n', '\\t', '\\r', '\\"', '\r\n', '\\r\\n', '\\']
    for special in specials:
        quoted_special = dtd.quotefordtd(special)
        unquoted_special = dtd.unquotefromdtd(quoted_special)
        print "special: %r\nquoted: %r\nunquoted: %r\n" % (special, quoted_special, unquoted_special)
        assert special == unquoted_special

class TestDTDUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = dtd.dtdunit

    
class TestDTD(test_monolingual.TestMonolingualStore):
    StoreClass = dtd.dtdfile
    def dtdparse(self, dtdsource):
        """helper that parses dtd source without requiring files"""
        dummyfile = wStringIO.StringIO(dtdsource)
        dtdfile = dtd.dtdfile(dummyfile)
        return dtdfile

    def dtdregen(self, dtdsource):
        """helper that converts dtd source to dtdfile object and back"""
        return str(self.dtdparse(dtdsource))

    def test_simpleentity(self):
        """checks that a simple dtd entity definition is parsed correctly"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.units) == 1
        dtdunit = dtdfile.units[0]
        assert dtdunit.entity == "test.me"
        assert dtdunit.definition == '"bananas for sale"'

    def test_blanklines(self):
        """checks that blank lines don't break the parsing or regeneration"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_simpleentity_source(self):
        """checks that a simple dtd entity definition can be regenerated as source"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_hashcomment_source(self):
        """checks that a #expand comment is retained in the source"""
        dtdsource = '#expand <!ENTITY lang.version "__MOZILLA_LOCALE_VERSION__">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_commentclosing(self):
        """tests that comment closes with trailing space aren't duplicated"""
        dtdsource = '<!-- little comment --> \n<!ENTITY pane.title "Notifications">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_commententity(self):
        """check that we don't process messages in <!-- comments -->: bug 102"""
        dtdsource = '''<!-- commenting out until bug 38906 is fixed
<!ENTITY messagesHeader.label         "Messages"> -->'''
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.units) == 1
        dtdunit = dtdfile.units[0]
        print dtdunit
        assert dtdunit.isnull()

    def test_newlines_in_entity(self):
        """tests that we can handle newlines in the entity itself"""
        dtdsource = '''<!ENTITY fileNotFound.longDesc "
<ul>
  <li>Check the file name for capitalisation or other typing errors.</li>
  <li>Check to see if the file was moved, renamed or deleted.</li>
</ul>
">
'''
        dtdregen = self.dtdregen(dtdsource)
        print dtdregen
        print dtdsource
        assert dtdsource == dtdregen

    def test_conflate_comments(self):
        """Tests that comments don't run onto the same line"""
        dtdsource = '<!-- test comments -->\n<!-- getting conflated -->\n<!ENTITY sample.txt "hello">\n'
        dtdregen = self.dtdregen(dtdsource)
        print dtdsource
        print dtdregen
        assert dtdsource == dtdregen

    def test_localisation_notes(self):
        """test to ensure that we retain the localisation note correctly"""
        dtdsource = '''<!--LOCALIZATION NOTE (publishFtp.label): Edit box appears beside this label -->
<!ENTITY publishFtp.label "If publishing to a FTP site, enter the HTTP address to browse to:">
'''
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_entitityreference_in_source(self):
        """checks that an &entity; in the source is retained"""
        dtdsource = '<!ENTITY % realBrandDTD SYSTEM "chrome://branding/locale/brand.dtd">\n%realBrandDTD;\n'
        dtdregen = self.dtdregen(dtdsource)
        print dtdsource
        print dtdregen
        assert dtdsource == dtdregen

    def wtest_comment_following(self):
        """check that comments that appear after and entity are not pushed onto another line"""
        dtdsource = '<!ENTITY textZoomEnlargeCmd.commandkey2 "="> <!-- + is above this key on many keyboards -->'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_comment_newline_space_closing(self):
        """check that comments that are closed by a newline then space then --> don't break the following entries"""
        dtdsource = '<!-- Comment\n -->\n<!ENTITY searchFocus.commandkey "k">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_invalid_quoting(self):
        """checks that invalid quoting doesn't work - quotes can't be reopened"""
        # TODO: we should rather raise an error
        dtdsource = '<!ENTITY test.me "bananas for sale""room">\n'
        assert dtd.unquotefromdtd(dtdsource[dtdsource.find('"'):]) == 'bananas for sale'
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.units) == 1
        dtdunit = dtdfile.units[0]
        assert dtdunit.definition == '"bananas for sale"'
        assert str(dtdfile) == '<!ENTITY test.me "bananas for sale">\n'

    def test_missing_quotes(self):
        """test that we fail graacefully when a message without quotes is found (bug #161)"""
        dtdsource = '<!ENTITY bad no quotes">\n<!ENTITY good "correct quotes">\n'
        dtdfile = self.dtdparse(dtdsource)
        # Check that we raise a correct warning
        assert len(dtdfile.units) == 1

