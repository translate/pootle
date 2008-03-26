#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import php
from translate.storage import test_monolingual
from translate.misc import wStringIO

def test_php_escaping():
    """Test the helper escaping funtions"""
    # Encoding
    assert php.phpencode("'") == "\\'"
    assert php.phpencode('"', quotechar='"') == '\\"'
    assert php.phpencode("\n") == "\\n"
    # Decoding
    assert php.phpdecode("\\'") == "'"
    assert php.phpdecode('\\"') == '"'
    assert php.phpdecode("\\n") == "\n"

class TestPhpUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = php.phpunit

    def test_difficult_escapes(self):
        pass

class TestPhpFile(test_monolingual.TestMonolingualStore):
    StoreClass = php.phpfile
    
    def phpparse(self, phpsource):
        """helper that parses php source without requiring files"""
        dummyfile = wStringIO.StringIO(phpsource)
        phpfile = php.phpfile(dummyfile)
        return phpfile

    def phpregen(self, phpsource):
        """helper that converts php source to phpfile object and back"""
        return str(self.phpparse(phpsource))

    def test_simpledefinition(self):
        """checks that a simple php definition is parsed correctly"""
        phpsource = """$lang['mediaselect'] = 'Bestand selectie';"""
        phpfile = self.phpparse(phpsource)
        assert len(phpfile.units) == 1
        phpunit = phpfile.units[0]
        assert phpunit.name == "$lang['mediaselect']"
        assert phpunit.source == "Bestand selectie"

    def test_simpledefinition_source(self):
        """checks that a simple php definition can be regenerated as source"""
        phpsource = """$lang['mediaselect']='Bestand selectie';"""
        phpregen = self.phpregen(phpsource)
        assert phpsource + '\n' == phpregen

    def test_spaces_in_name(self):
        """check that spaces in the array name doesn't throw us off"""
        phpsource =  """$lang[ 'mediaselect' ] = 'Bestand selectie';"""
        phpfile = self.phpparse(phpsource)
        assert len(phpfile.units) == 1
        phpunit = phpfile.units[0]
        assert phpunit.name == "$lang['mediaselect']"
        assert phpunit.source == "Bestand selectie"
