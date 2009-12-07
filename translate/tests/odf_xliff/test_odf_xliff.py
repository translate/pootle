#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import os.path as path
import zipfile

from lxml import etree
import difflib

from translate.storage import factory
from translate.convert import odf2xliff
from translate.convert import xliff2odf

def setup_module(module):
    os.chdir(path.dirname(__file__))

def args(src, tgt, **kwargs):
    arg_list = [u'--psyco=none', u'--errorlevel=traceback', src, tgt]
    for flag, value in kwargs.iteritems():
        value = unicode(value)
        if len(flag) == 1:
            arg_list.append(u'-%s' % flag)
        else:
            arg_list.append(u'--%s' % flag)
        if value is not None:
            arg_list.append(value)
    return arg_list

def xliff___eq__(self, other):
    return self.units == other.units

factory.classes[u'xlf'].__eq__ = xliff___eq__

def print_diff(store1, store2):
    for line in difflib.unified_diff(str(store1).split('\n'), str(store2).split('\n')):
        print line

SOURCE_ODF            = u'test_2.odt'
REFERENCE_XLF         = u'test_2-test_odf2xliff-reference.xlf'
GENERATED_XLF_ITOOLS  = u'test_2-test_odf2xliff-itools.xlf'
GENERATED_XLF_TOOLKIT = u'test_2-test_odf2xliff-toolkit.xlf'

TARGET_XLF    = u'test_2-test_roundtrip.xlf'
REFERENCE_ODF = u'test_2.odt'
GENERATED_ODF = u'test_2-test_roundtrip-generated.odt'

def test_odf2xliff():
    reference_xlf = factory.getobject(REFERENCE_XLF)

    odf2xliff.main(args(SOURCE_ODF, GENERATED_XLF_TOOLKIT))
    generated_xlf_toolkit = factory.getobject(GENERATED_XLF_TOOLKIT)
    print_diff(reference_xlf, generated_xlf_toolkit)
    assert reference_xlf == generated_xlf_toolkit

    odf2xliff.main(args(SOURCE_ODF, GENERATED_XLF_ITOOLS))
    generated_xlf_itools = factory.getobject(GENERATED_XLF_ITOOLS)
    print_diff(reference_xlf, generated_xlf_itools)
    assert reference_xlf == generated_xlf_itools

def is_content_file(filename):
    return filename in (u'content.xml', u'meta.xml', u'styles.xml')

class ODF(object):
    def __init__(self, filename):
        self.odf = zipfile.ZipFile(filename)

    def _get_data(self, filename):
        return self.odf.read(filename)

    def _get_doc_root(self, filename):
        return etree.tostring(etree.fromstring(self._get_data(filename)), encoding="UTF-8")

    def __eq__(self, other):
        if other == None:
            return False
        l1 = set(zi.filename for zi in self.odf.infolist())
        l2 = set(zi.filename for zi in other.odf.infolist())
        if l1 != l2:
            return False
        for filename in l1:
            if is_content_file(filename):
                l = self._get_doc_root(filename)
                r = other._get_doc_root(filename)
                if self._get_doc_root(filename) != other._get_doc_root(filename):
                    return False
            else:
                if self._get_data(filename) != other._get_data(filename):
                    return False
        return True

    def __str__(self):
        return self.odf.read('content.xml')

def test_roundtrip():

    odf2xliff.main(args(SOURCE_ODF, TARGET_XLF))
    xliff2odf.main(args(TARGET_XLF, GENERATED_ODF, t=SOURCE_ODF))

    reference_odf = ODF(REFERENCE_ODF)
    generated_odf = ODF(GENERATED_ODF)

    print_diff(reference_odf, generated_odf)
    assert reference_odf == generated_odf

def remove(filename):
    """Removes the file if it exists."""
    if os.path.exists(filename):
        os.unlink(filename)

def teardown_module(module):
    remove(GENERATED_XLF_TOOLKIT)
    remove(GENERATED_ODF)
    remove(GENERATED_XLF_ITOOLS)
    remove(TARGET_XLF)

if __name__ == '__main__':
    setup_module(None)
    test_roundtrip()
    teardown_module(None)

