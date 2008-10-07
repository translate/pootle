#!/usr/bin/env python
# -*- coding: utf-8 -*

#Copyright (c) 2006 - 2007 by The WordForge Foundation
#                       www.wordforge.org
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# See the LICENSE file for more details. 
#
# Developed by:
#       Hok Kakada (hokkakada@khmeros.info)
#       Keo Sophon (keosophon@khmeros.info)
#       San Titvirak (titvirak@khmeros.info)
#       Seth Chanratha (sethchanratha@khmeros.info)
# 
# This module is working on tests for PickleTM classes

from PyQt4 import QtCore, QtGui
from translate.search import match
from translate.storage import po
from translate.storage import xliff

import os, sys
import unittest
import tempfile
from pootling.modules.pickleTM import pickleTM

class Test_pickleTM(unittest.TestCase):
    def setUp(self):
        self.pickle = pickleTM()
        handle, self.pickleFile = tempfile.mkstemp('','PKL')
        self.message = '''# aaaaa
#: kfaximage.cpp:189
#, fuzzy
msgid "Unable to open file for reading."
msgstr "unable, to read file"

#: archivedialog.cpp:126
msgid "Could not open a temporary file"
msgstr "Could not open any"
'''
        store = po.pofile.parsestring(self.message)
        self.matcher = match.matcher(store, 10, 75, 300)
        
    def testGetMatcherXLF(self):
        """Test that it can pickle and unpickle xliff matcher"""
        XMLskeleton = '''<?xml version="1.0" ?>
<xliff version='1.1' xmlns='urn:oasis:names:tc:xliff:document:1.1'>
 <file original='NoName' source-language='en' datatype='plaintext'>
  <body>
  </body>
 </file>
</xliff>'''
        store = xliff.xlifffile.parsestring(XMLskeleton)
        matcher = match.matcher(store, 10, 75, 300)
        self.pickle.dumpMatcher(matcher, self.pickleFile)
        # if file exists.
        matcher = self.pickle.getMatcher(self.pickleFile)
        self.assertEqual(type(matcher), type(self.matcher))
        os.remove(self.pickleFile)
        
        # if file doesn't exists.
        matcher = self.pickle.getMatcher("/tmp/testPLK")
        self.assertEqual(matcher, None)
        
    def testGetMatcherPO(self):
        """Test that we can pickle and unpickle the PO matcher back."""
        self.pickle.dumpMatcher(self.matcher, self.pickleFile)
        # if file exists.
        matcher = self.pickle.getMatcher(self.pickleFile)
        self.assertEqual(type(matcher), type(self.matcher))
        
        os.remove(self.pickleFile)
        
        # if file doesn't exists.
        matcher = self.pickle.getMatcher("/tmp/testPLK")
        self.assertEqual(matcher, None)
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    unittest.main()
    
