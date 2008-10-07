#!/usr/bin/env python

from translate.convert import odf2po
from translate.convert import test_convert

class TestODF2PO:
    pass

class TestODF2POCommand(test_convert.TestConvertCommand, TestODF2PO):
    """Tests running actual odf2po commands on files"""
    convertmodule = odf2po

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "", last=True)
