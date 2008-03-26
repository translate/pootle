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
# This module is working on tests for Operator classes


import sys
import os
import unittest
import time
import Operator
import Status
import World
import tempfile
from translate.storage import factory
from translate.misc import wStringIO
from translate.storage import po
from PyQt4 import QtCore, QtGui
from pootling import __version__

class TestOperator(unittest.TestCase):
    def setUp(self):
        self.operator = Operator.Operator()
        self.slotReached = False
        self.callCount = 0
        self.message = """# aaaaa
#: kfaximage.cpp:189
#, fuzzy
msgid "Unable to open file for reading."
msgstr "unable, to read file"

#: archivedialog.cpp:126
msgid "Could not open a temporary file"
msgstr "Could not open any"
"""
        self.arg0 = None
        self.arg1 = None
        self.arg2 = None
        
    def testSetNewStore(self):
        """
        Test the following signals in setNewStore are called.
        """
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("newUnits"), self.slot)
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("currentUnit"), self.slot)
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("currentStatus"), self.slot)
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        self.assertEqual(self.slotReached, True)
        self.assertEqual(self.callCount, 3)
        self.assertEqual(self.operator.modified, False)
    
    def testEmitStatus(self):
        """
        Test "currentStatus" signal is emitted with a list contains total,
        fuzzy, translated, and untranslated messages of current file.
        """
        self.operator.status = Status.Status(po.pofile.parsestring(self.message))
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("currentStatus"), self.slot)
        self.operator.emitStatus()
        self.assertEqual(self.callCount, 1)
        self.assertEqual(type(self.arg0), list)
        self.assertEqual(self.arg1, None)
##        self.assertEqual(self.operator.status.numTranslated, 1)
##        self.assertEqual(self.operator.status.numFuzzy, 1)
##        self.assertEqual(self.operator.status.numUntranslated, 0)
    
    def testEmitUnit(self):
        """
        Test "currentUnit" signal is emitted.
        """
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("currentUnit"), self.slot)
        unit = po.pofile.parsestring(self.message).units[0]
        
        # test case unit has no attribute x_editor_filterIndex
        self.operator.emitUnit(unit)
        self.assertEqual(self.operator.currentUnitIndex, 0)
        self.assertEqual(self.slotReached, True)
        
        # test case unit has attribute x_editor_filterIndex
        unit.x_editor_filterIndex = 1
        self.operator.emitUnit(unit)
        self.assertEqual(self.operator.currentUnitIndex, 1)
        self.assertEqual(self.slotReached, True)
        
    def testFilterFuzzy(self):
        """
        Test we can add/remove fuzzy to filter, and send filter signal.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("filterChanged"), self.slot)
        self.operator.filter = World.filterAll
        
        # test if filter fuzzy is checked
        self.operator.filterFuzzy(True)
        self.assertEqual(self.operator.filter, World.filterAll)
        
        # test if filter fuzzy is unchecked
        self.operator.filterFuzzy(False)
        self.assertEqual(self.operator.filter, World.filterAll - World.fuzzy)
        self.assertEqual(self.callCount, 2)
    
    def testFilterTranslated(self):
        """
        Test we can add/remove translated to filter, and send filter signal.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("filterChanged"), self.slot)
        self.status = Status.Status(self.operator.store)
        
        self.operator.filter = World.filterAll
        # test if filter translated is checked
        self.operator.filterTranslated(True)
        self.assertEqual(self.operator.filter, World.filterAll)
        
        # test if filter translated is unchecked
        self.operator.filterTranslated(False)
        self.assertEqual(self.operator.filter, World.filterAll - World.translated)
        self.assertEqual(self.callCount, 2)
    
    def testFilterUntranslated(self):
        """
        Test we can add/remove untranslated to filter, and send filter signal.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("filterChanged"), self.slot)
        self.status = Status.Status(self.operator.store)
        
        self.operator.filter = World.filterAll
        # test if filter untranslated is checked
        self.operator.filterUntranslated(True)
        self.assertEqual(self.operator.filter, World.filterAll)
       
        # test if filter untranslated is unchecked
        self.operator.filterUntranslated(False)
        self.assertEqual(self.operator.filter, World.filterAll - World.untranslated)
        self.assertEqual(self.slotReached, True)
        self.assertEqual(self.callCount, 2)
    
    def testEmitFiltered(self):
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("filterChanged"), self.slot)
        self.operator.emitFiltered(World.filterAll)
        self.assertEqual(self.slotReached, True)
        
    def testEmitNewUnit(self):
        """
        Test that the 'newUnits' is emitted only if have units.
        """
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("newUnits"), self.slot)
     
        # test case self.store is valid
        self.operator.store = po.pofile.parsestring(self.message)
        self.operator.setNewStore(self.operator.store)
        self.operator.emitNewUnits()
        self.assertEqual(self.slotReached, True)
     
        # test case self.store is none
        self.operator.store = None
        self.operator.setNewStore(self.operator.store)
        self.slotReached = False
        self.operator.emitNewUnits()
        self.assertEqual(self.arg0, [])
        
    def testHeaderData(self):
        """
        Test we can get the correct header info from the file.
        """
    
        # test message Header which has no data
        self.operator.store = po.pofile.parsestring(self.message)
        self.assertEqual(self.operator.headerData(), ('', {}))
     
        # test message Header which has data
        message = """msgid ""
msgstr ""
"POT-Creation-Date: 2005-05-18 21:23+0200\n"
"PO-Revision-Date: 2006-11-27 11:50+0700\n"
"Project-Id-Version: cupsdconf\n"
""
# aaaaa
#: kfaximage.cpp:189
msgid "Unable to open file for reading."
msgstr "unable to read file"
"""
        self.operator.store = po.pofile.parsestring(message)
        self.assertEqual(self.operator.headerData(), ('', {'POT-Creation-Date': u'2005-05-18 21:23+0200', 'PO-Revision-Date': u'2006-11-27 11:50+0700', 'Project-Id-Version': u'cupsdconf'}))
    
    def testMakeNewHeader(self):
        """
        Test it really creates a new header based on a given information in headerDic.
        """
        
        headerDic = {'charset':"CHARSET", 'encoding':"ENCODING", 'project_id_version': 'pootling.po', 'pot_creation_date':None, 'po_revision_date': False, 'last_translator': 'AAA', 'language_team': 'KhmerOS', 'mime_version':None, 'plural_forms':None, 'report_msgid_bugs_to':None}
        
        # test self.store is not instance of poheader.poheader()
        self.store = None
        self.assertEqual(self.operator.makeNewHeader(headerDic), {})
        
        # test self.store is instance of poheader.poheader()
        self.operator.store = po.pofile.parsestring(self.message)
        result = {'PO-Revision-Date': time.strftime("%Y-%m-%d %H:%M") + self.operator.store.tzstring(), 'X-Generator': World.settingApp + ' ' + __version__.ver, 'Content-Transfer-Encoding': 'ENCODING', 'Plural-Forms': 'nplurals=INTEGER; plural=EXPRESSION;', 'Project-Id-Version': 'pootling.po', 'Report-Msgid-Bugs-To': '', 'Last-Translator': 'AAA', 'Language-Team': 'KhmerOS', 'POT-Creation-Date': time.strftime("%Y-%m-%d %H:%M") + self.operator.store.tzstring(), 'Content-Type': 'text/plain; charset=CHARSET', 'MIME-Version': '1.0'}
        self.assertEqual(self.operator.makeNewHeader(headerDic), result)
        self.assertEqual(self.operator.store.x_generator, World.settingApp + ' ' + __version__.ver)
    
    def testUpdateNewHeader(self):
        """
        Test that it will update the existing header.
        """
        message = """msgid ""
msgstr ""
"POT-Creation-Date: 2005-05-18 21:23+0200\n"
"PO-Revision-Date: 2006-11-27 11:50+0700\n"
"Project-Id-Version: cupsdconf\n"
""
# aaaaa
#: kfaximage.cpp:189
msgid "Unable to open file for reading."
msgstr "unable to read file"
"""
        # test self.store is not instance of poheader.poheader()
        self.store = None
        self.assertEqual(self.operator.updateNewHeader(None, None), {})
        
        # test self.store is instance of poheader.poheader()
        self.operator.store = po.pofile.parsestring(message)
        otherComment = "hello comment"
        headerDic = {"POT-Creation-Date":" 2005-05-18 21:23+0200",
"PO-Revision-Date":" 2007-02-22 11:50+0700",
"Project-Id-Version": "cupsdconf_new", "AAA":"BBB"}
        self.operator.updateNewHeader(otherComment, headerDic)
        self.assertEqual(self.operator.store.header().getnotes(), "hello comment")
        result = u'Project-Id-Version: cupsdconf_new\nReport-Msgid-Bugs-To: \nPOT-Creation-Date:  2005-05-18 21:23+0200\nPO-Revision-Date:  2007-02-22 11:50+0700\nLast-Translator: FULL NAME <EMAIL@ADDRESS>\nLanguage-Team: LANGUAGE <LL@li.org>\nMIME-Version: 1.0\nContent-Type: text/plain; charset=CHARSET\nContent-Transfer-Encoding: ENCODING\nPlural-Forms: nplurals=INTEGER; plural=EXPRESSION;\nX-Generator: ' + self.operator.store.x_generator + '\nAAA: BBB\n'
        self.assertEqual(self.operator.store.header().target, result)
        
    def testSaveStoreToFile(self):
        """
        Test it will save the temporary store into a file.
        """
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("headerAuto"), self.slot)
        self.operator.store = po.pofile.parsestring(self.message)
        
        handle, filename = tempfile.mkstemp('.po')
        
        # test headerAuto value is True
        World.settings.setValue("headerAuto", QtCore.QVariant(True))
        self.operator.saveStoreToFile(filename)
        self.assertEqual(self.slotReached, True)
        self.assertEqual(len(factory.getobject(filename).units), 2)
        self.assertEqual(self.operator.modified, False)
#        self.assertEqual(self.operator.headerData, ("hello",{"Project-Id-Version": "Pootling.po", "AAA":"BBB"}))
        
        # test headerAuto is False
        self.slotReached = False
        World.settings.setValue("headerAuto", QtCore.QVariant(False))
        self.operator.saveStoreToFile(filename)
        self.assertEqual(self.slotReached, False)
        self.assertEqual(self.operator.modified, False)
        
        os.remove(filename)
        
    def testIsModified(self):
        """
        Test the isModified interface is correct.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        # test it will return True, if modified is true
        self.operator.modified = True
        self.assertEqual(self.operator.isModified(), True)
        
        # test it will return False, if modified is False
        self.operator.modified = False
        self.assertEqual(self.operator.isModified(), False)
        
    def testSetComment(self):
        """
        Test we can set comment to the store correctly.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        # Test if there is no unit
        self.operator.currentUnitIndex = -1
        self.operator.setComment("comments")
        self.assertEqual(self.operator.filteredList[self.operator.currentUnitIndex].getnotes(), "")
        self.assertEqual(self.operator.modified, False)
        
        # Test if there is a least a unit
        self.operator.currentUnitIndex = 1
        self.operator.setComment("comments")
        self.assertEqual(self.operator.filteredList[self.operator.currentUnitIndex].getnotes(), u"comments")
        self.assertEqual(self.operator.modified, True)
    
    def testSetTarget(self):
        """
        Test we can set target to the store correctly.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        # TODO: Test if there is no translation unit in the view.
        
        # Test if there is translation unit in the view.
        self.operator.currentUnitIndex = 1
        self.operator.setTarget("target")
        self.assertEqual(self.operator.filteredList[self.operator.currentUnitIndex].target, u"target")
        #TODO: test with plural unit.
    
    def testToggleFuzzy(self):
        """
        Test toggle fuzzy state for current unit is working correctly.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        # the unit is first fuzzy, call toggleFuzzy(), the unit must not be fuzzy
        self.operator.toggleFuzzy()
        self.assertEqual(self.operator.store.units[0].isfuzzy(), False)
        # calling toggleFuzzy() again, the unit must be fuzzy again.
        self.operator.toggleFuzzy()
        self.assertEqual(self.operator.store.units[0].isfuzzy(), True)
    
    def testInitSearch(self):
        """
        Test the initilized variables for searching.
        """
        self.operator.initSearch("Aaa", [World.source, World.target, World.comment], False)
        self.assertEqual(self.operator.searchString, u"Aaa")
        self.assertEqual(self.operator.searchFields, [World.source, World.target, World.comment])
        self.assertEqual(self.operator.matchCase, False)
        
    def testSearchNext(self):
        """
        Test search forward through the text fields.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        self.operator.searchStartIndex = 0
        self.operator.initSearch('To', [World.source, World.target, World.comment], False)
        
        # first found search will encounter in source
        self.operator.searchNext()
        self.assertEqual(self.operator.foundPosition, 7)
        
        # second found search will encounter in target
        self.operator.searchNext()
        self.assertEqual(self.operator.foundPosition, 8)
        
        # then search will not found and reached end of units
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("searchStatus"), self.slot)
        self.operator.searchNext()
        self.assertEqual(self.slotReached, True)
        self.assertEqual(self.arg0, "reachedEnd")
    
    def testSearchPrevious(self):
        """
        Test search backward through the text fields.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        self.operator.searchStartIndex = 1
        self.operator.initSearch('To', [World.source, World.target, World.comment], False)
        
        # first found search will encounter in target
        self.operator.searchPrevious()
        self.assertEqual(self.operator.foundPosition, 8)
        
        # second found search will encounter in source
        self.operator.searchPrevious()
        self.assertEqual(self.operator.foundPosition, 7)
        
        # then search will not found and read the beginning of units
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("searchStatus"), self.slot)
        self.operator.searchPrevious()
        self.assertEqual(self.slotReached, True)
        self.assertEqual(self.arg0, "reachedEnd")
    
    def testReplace(self):
        """
        Test that we cannot replace in textSource. and found position start from -1.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        QtCore.QObject.connect(self.operator, QtCore.SIGNAL("replaceText"), self.slot)
        self.operator.initSearch("unable,", [World.target, World.comment], False)
        self.operator.searchNext()
        self.operator.replace("to")
        self.assertEqual(self.slotReached, True)
        self.assertEqual(self.operator.currentField, World.target)
        self.assertEqual(self.operator.foundPosition, -1)
    
    def test_getStringFromUnit(self):
        """
        Test we will get the correct unit string.
        """
        self.operator.setNewStore(po.pofile.parsestring(self.message))
        self.operator.searchableText = [World.source, World.target]
        self.operator.matchCase = True
        # get string in target
        unit = self.operator.store.units[0]
        self.assertEqual(self.operator._getStringFromUnit(unit, World.target), u"unable, to read file")
        # get string in source
        self.assertEqual(self.operator._getStringFromUnit(unit, World.source), u"Unable to open file for reading.")
    
    def slot(self, arg0 = None, arg1 = None, arg2 = None):
        self.slotReached = True
        self.callCount += 1
        self.arg0 = arg0
        self.arg1 = arg1
        self.arg2 = arg2
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    unittest.main()
