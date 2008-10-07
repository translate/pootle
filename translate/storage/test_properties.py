#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import properties
from translate.storage import test_monolingual
from translate.misc import wStringIO

class TestPropUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = properties.propunit

    def test_difficult_escapes(self):
        """It doesn't seem that properties files can store double backslashes.
        
        We are disabling the double-backslash tests for now.
        If we are mistaken in the above assumption, we need to fix getsource()
        and setsource() and delete this test override.
        
        """
        pass

class TestProp(test_monolingual.TestMonolingualStore):
    StoreClass = properties.propfile
    
    def propparse(self, propsource):
        """helper that parses properties source without requiring files"""
        dummyfile = wStringIO.StringIO(propsource)
        propfile = properties.propfile(dummyfile)
        return propfile

    def propregen(self, propsource):
        """helper that converts properties source to propfile object and back"""
        return str(self.propparse(propsource))

    def test_simpledefinition(self):
        """checks that a simple properties definition is parsed correctly"""
        propsource = 'test_me=I can code!'
        propfile = self.propparse(propsource)
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == "test_me"
        assert propunit.source == "I can code!"

    def test_simpledefinition_source(self):
        """checks that a simple properties definition can be regenerated as source"""
        propsource = 'test_me=I can code!'
        propregen = self.propregen(propsource)
        assert propsource + '\n' == propregen

    def test_unicode_escaping(self):
        """check that escapes unicode is converted properly"""
        propsource = "unicode=\u0411\u0416\u0419\u0428"
        messagevalue = u'\u0411\u0416\u0419\u0428'.encode("UTF-8")
        propfile = self.propparse(propsource)
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == "unicode"
        assert propunit.source.encode("UTF-8") == "БЖЙШ"
        regensource = str(propfile)
        assert messagevalue in regensource
        assert "\\u" not in regensource

    def test_newlines_startend(self):
        """check that we preserver \n that appear at start and end of properties"""
        propsource = "newlines=\\ntext\\n"
        propregen = self.propregen(propsource)
        assert propsource + '\n' == propregen

    def test_whitespace_removal(self):
        """check that we remove extra whitespace around property"""
        propsource = '''  whitespace  =  Start \n'''
        propfile = self.propparse(propsource)
        propunit = propfile.units[0]
        assert propunit.name == "whitespace"
        assert propunit.source == "Start"
     
