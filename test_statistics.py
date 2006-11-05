#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests for stats classes"""

from py import test
from Pootle import statistics
from translate.storage import po
import os

class TestStatsFile:
    """Tests StatsFile"""

    def test_creation(self):
        """we create the object and storage file correctly"""
        pofile = po.pofile()
        pofile.filename = "file/test.po"
        sfile = statistics.StatsFile(pofile)
        assert sfile.filename == "file/test.po.stats"

    def test_hasparent(self):
        """check that we manage the associated stats file for a translatable file"""
        posource = '''msgid "Simple String"\nmsgstr "Dimpled ring"\n'''
        pofile = open("test.po", "w")
        pofile.write(posource)
        pofile.close()
        pofile = open("test.po", "r")
        poobj = po.pofile(pofile)
        print poobj
        sfile = statistics.StatsFile(poobj)
        assert sfile.hasparent() == True
        os.remove("test.po")
        assert not sfile.hasparent()
        assert not os.path.exists("test.po.stats")
        
