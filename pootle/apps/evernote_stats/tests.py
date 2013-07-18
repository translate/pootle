#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation

import unittest
from util import diff_stat

import json

OLD = 'old'
NEW = 'new'
RES0 = 'res0'
RES1 = 'res1'

data = [
    {OLD: '', NEW: '', RES0: [0,0], RES1: [0,0]},
    {OLD: '', NEW: 'qwerty', RES0: [1,0], RES1: [6,0]},
    {OLD: 'qwerty', NEW: 'qwerty', RES0: [0,0], RES1: [0,0]},
    {OLD: 'qwerty', NEW: '', RES0: [0,1], RES1: [0,6]},
    {OLD: 'qwerty', NEW: 'ytrewq', RES0: [1,1], RES1: [5,5]},
    {OLD: 'Moscow Kiev Minsk', NEW: 'Kiev Minsk Moscow', RES0: [1,1], RES1: [7,7]},
    {OLD: 'Moscow Kiev Minsk Riga', NEW: 'Minsk Kiev Riga Moscow', RES0: [3,3], RES1: [16,16]},
    {OLD: 'Moscow Kiev Minsk Riga Vilnus', NEW: 'Minsk Kiev Riga Vilnus Moscow', RES0: [2,2], RES1: [10,10]},
    {OLD: '<a href="/download">Download Mars</a>', NEW: '<a href="/download">download Mars</a>', RES0: [1,1], RES1: [1,1]},
    {OLD: '<a href="/download">DOWNLOAD Mars</a>', NEW: '<a href="/download"> Download from Mars</a>', RES0: [3,1], RES1: [13,7]},
    {OLD: 'foo bar baz', NEW: 'foo etc baz', RES0: [1,1], RES1: [3,3]},
    {OLD: "foo\nbar\nbaz", NEW: "foo\netc\nbaz", RES0: [1,1], RES1: [3,3]}
]


class DiffStatTestCase(unittest.TestCase):
    def __init__(self, old_words, new_words, expected):
        super(DiffStatTestCase, self).__init__()
        self.old_words = old_words
        self.new_words = new_words
        self.expected = expected
        
    def runTest(self):
        res = diff_stat(self.old_words, self.new_words)
        self.assertEqual(res, self.expected)
            
    
def suite():
    suite = unittest.TestSuite()
    suite.addTests(DiffStatTestCase(item[OLD].split(), item[NEW].split(), item[RES0]) for item in data)
    suite.addTests(DiffStatTestCase(item[OLD], item[NEW], item[RES1]) for item in data)
    
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())