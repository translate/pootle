#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""tests for stats classes"""

from py import test
from Pootle import statistics
from translate.storage import po

class TestStatsFile:
    """Tests StatsFile"""
    def test_creation(self):
        """we create the object and storage file correctly"""
        pofile = po.pofile()
        pofile.filename = "file/test.po"
        sfile = statistics.StatsFile(pofile)
        assert sfile.filename == "file/test.po.stats"
