#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import os

import pytest

from django.test import TestCase

from pootle.core.initdb import require_english

from pootle_project.models import Project
from pootle_store.models import Store
from pootle_app.project_tree import get_translated_name, get_translated_name_gnu
from pootle_language.models import Language
from pootle_store.util import OBSOLETE


pytestmark = pytest.mark.xfail


class GnuTests(TestCase):
    """Tests for Gnu Style projects"""

    template_text = r'''msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"Report-Msgid-Bugs-To: \n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"X-Generator: Pootle Tests\n"

#: fish.c:1
msgid "Exact"
msgstr ""

#: test.c:1
msgid "Fuzzy"
msgstr ""

#: fish.c:2
msgid "%d new"
msgid_plural "%d news"
msgstr[0] ""
msgstr[1] ""
'''

    target_text = r'''msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"Report-Msgid-Bugs-To: \n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"X-Generator: Pootle Tests\n"

#: fish.c:1
msgid "Exact"
msgstr "Belzabt"

#: test.c:1
msgid "fuzzy"
msgstr "ta2riban"

#: fish.c:2
msgid "obsolete"
msgstr "2adim"
'''

    def _setup_test_files(self):
        gnu = os.path.join(self.testpodir, "testproj")
        os.mkdir(gnu)
        potfile = file(os.path.join(gnu, "test.pot"), 'w')
        potfile.write(self.template_text)
        potfile.close()
        pofile = file(os.path.join(gnu, "ar.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnu, "af.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnu, "zu.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnu, "pt_br.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        gnusub = os.path.join(gnu, "subdir")
        os.mkdir(gnusub)
        potfile = file(os.path.join(gnusub, "test.pot"), 'w')
        potfile.write(self.template_text)
        potfile.close()
        pofile = file(os.path.join(gnusub, "ar.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnusub, "af.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnusub, "zu.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnusub, "pt_br.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()

    def setUp(self):
        super(GnuTests, self).setUp()
        en = require_english()
        Project.objects.get_or_create(code="testproj", fullname=u"testproj",
                                      source_language=en)
        self.project = Project.objects.get(code='testproj')
        for tp in self.project.translationproject_set.iterator():
            tp.require_units()

    def test_treestyle(self):
        """test treestyle detection"""
        self.assertEqual(self.project.get_treestyle(), 'gnu')

    def test_realpath(self):
        """test that physical path is calculated correctly"""
        for tp in self.project.translationproject_set.iterator():
            self.assertEqual(tp.real_path, u'testproj')

    def test_file_detection(self):
        """test correct language detection when a project is added"""
        lang_count = self.project.translationproject_set.count()
        self.assertEqual(lang_count, 5)

        store_count = Store.objects.filter(translation_project__project=self.project).count()
        self.assertEqual(store_count, 10)

        lang_list = list(self.project.translationproject_set.values_list('language__code', flat=True).order_by('language__code'))
        self.assertEqual(lang_list, [u'af', u'ar', u'pt_BR', u'templates', u'zu'])

    def test_template_detection(self):
        """test that given a template the correct target file name is generated"""
        template_tp = self.project.get_template_translationproject()
        for template_store in template_tp.stores.iterator():
            for tp in self.project.translationproject_set.exclude(language__code='templates').iterator():
                new_pootle_path, new_path = get_translated_name_gnu(tp, template_store)
                store = tp.stores.get(pootle_path=new_pootle_path)
                self.assertEqual(new_pootle_path, store.pootle_path)
                self.assertEqual(new_path, store.abs_real_path)

    def test_new(self):
        """test initializing a new file from templates"""
        fr = Language.objects.get(code='fr')
        new_tp = self.project.translationproject_set.create(language=fr)
        new_tp.update_against_templates()
        store_count = new_tp.stores.count()
        self.assertEqual(store_count, 2)
        store = new_tp.stores.all()[0]
        dbunit_count = store.units.count()
        self.assertEqual(dbunit_count, 3)
        stunit_count = len(store.file.store.units)
        self.assertEqual(stunit_count, 4)

    def test_update(self):
        """test updating existing files to templates"""
        tp = self.project.translationproject_set.get(language__code='ar')
        tp.update_against_templates()

        store_count = tp.stores.count()
        self.assertEqual(store_count, 2)

        store = tp.stores.all()[0]
        dbunit_count = store.units.count()
        self.assertEqual(dbunit_count, 3)

        stunit_count = len(store.file.store.units)
        self.assertEqual(stunit_count, 6)

        unit = store.findid('Exact')
        self.assertEqual(unit.target, u'Belzabt')
        self.assertFalse(unit.isfuzzy())

        unit = store.findid('Fuzzy')
        self.assertEqual(unit.target, u'ta2riban')
        self.assertTrue(unit.isfuzzy())

        unit = store.findid('%d new')
        self.assertFalse(unit.istranslated())

        obsolete_count = store.unit_set.filter(state=OBSOLETE).count()
        self.assertEqual(obsolete_count, 1)
        unit = store.unit_set.get(state=OBSOLETE, unitid='obsolete')
        self.assertEqual(unit.source, u'obsolete')
        self.assertEqual(unit.target, u'2adim')
        #for unit in store.file.store.units:
        #    if unit.isobsolete():
        #        unit.resurrect()
        #        self.assertEqual(unit.source, u'obsolete')
        #        self.assertEqual(unit.target, u'2adim')

class PrefixGnuTests(GnuTests):
    """tests for Gnu style with prefix projects"""

    def _setup_test_files(self):
        gnu = os.path.join(self.testpodir, "testproj")
        os.mkdir(gnu)
        potfile = file(os.path.join(gnu, "test.pot"), 'w')
        potfile.write(self.template_text)
        potfile.close()
        pofile = file(os.path.join(gnu, "test_ar.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnu, "test_af.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnu, "test_zu.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnu, "test_pt_br.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        gnusub = os.path.join(gnu, "subdir")
        os.mkdir(gnusub)
        potfile = file(os.path.join(gnusub, "test.pot"), 'w')
        potfile.write(self.template_text)
        potfile.close()
        pofile = file(os.path.join(gnusub, "test_ar.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnusub, "test_af.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnusub, "test_zu.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnusub, "test_pt_br.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()


class NonGnuTests(GnuTests):
    """tests for Non-Gnu style projects"""

    def _setup_test_files(self):
        nongnu = os.path.join(self.testpodir, "testproj")
        os.mkdir(nongnu)
        nongnu_templates = os.path.join(nongnu, "templates")
        os.mkdir(nongnu_templates)
        nongnu_ar = os.path.join(nongnu, "ar")
        os.mkdir(nongnu_ar)
        nongnu_af = os.path.join(nongnu, "af")
        os.mkdir(nongnu_af)
        nongnu_zu = os.path.join(nongnu, "zu")
        os.mkdir(nongnu_zu)
        nongnu_pt_br = os.path.join(nongnu, "pt_BR")
        os.mkdir(nongnu_pt_br)

        potfile = file(os.path.join(nongnu_templates, "test.pot"), 'w')
        potfile.write(self.template_text)
        potfile.close()
        pofile = file(os.path.join(nongnu_ar, "test.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(nongnu_af, "test.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(nongnu_zu, "test.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(nongnu_pt_br, "test.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()

        nongnusub_templates = os.path.join(nongnu_templates, "subdir")
        os.mkdir(nongnusub_templates)
        nongnusub_ar = os.path.join(nongnu_ar, "subdir")
        os.mkdir(nongnusub_ar)
        nongnusub_af = os.path.join(nongnu_af, "subdir")
        os.mkdir(nongnusub_af)
        nongnusub_zu = os.path.join(nongnu_zu, "subdir")
        os.mkdir(nongnusub_zu)
        nongnusub_pt_br = os.path.join(nongnu_pt_br, "subdir")
        os.mkdir(nongnusub_pt_br)

        potfile = file(os.path.join(nongnusub_templates, "test.pot"), 'w')
        potfile.write(self.template_text)
        potfile.close()
        pofile = file(os.path.join(nongnusub_ar, "test.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(nongnusub_af, "test.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(nongnusub_zu, "test.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(nongnusub_pt_br, "test.po"), 'w')
        pofile.write(self.target_text)
        pofile.close()

    def test_realpath(self):
        """test that physical path is calculated correctly"""
        for tp in self.project.translationproject_set.iterator():
            expected_path = u'testproj/%s' % tp.language.code
            self.assertEqual(tp.real_path, expected_path)

    def test_template_detection(self):
        """test that given a template the correct target file name is generated"""
        template_tp = self.project.get_template_translationproject()
        for template_store in template_tp.stores.iterator():
            for tp in self.project.translationproject_set.exclude(language__code='templates').iterator():
                new_pootle_path, new_path = get_translated_name(tp, template_store)
                store = tp.stores.get(pootle_path=new_pootle_path)
                self.assertEqual(new_pootle_path, store.pootle_path)
                self.assertEqual(new_path, store.abs_real_path)

    def test_treestyle(self):
        """test treestyle detection"""
        self.assertEqual(self.project.get_treestyle(), 'nongnu')


class XliffTests(TestCase):
    """tests for XLIFF projects"""

    template_text = r'''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
    <file original="doc.txt" source-language="en-US">
        <body>
            <trans-unit xml:space="preserve" id="header" approved="no" restype="x-gettext-domain-header">
                <source>Project-Id-Version: PACKAGE VERSION
Report-Msgid-Bugs-To:
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
X-Generator: Pootle Tests
</source>
                <target state="translated">Project-Id-Version: PACKAGE VERSION
Report-Msgid-Bugs-To:
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
X-Generator: Pootle Tests
</target>
            </trans-unit>
            <trans-unit id="Exact"><source>Exact</source><target></target></trans-unit>
            <trans-unit id="Fuzzy"><source>Fuzzy</source><target></target></trans-unit>
            <group id="1" restype="x-gettext-plurals">
                <trans-unit id="1[0]"><source>%d new</source><target></target></trans-unit>
                <trans-unit id="1[1]"><source>%d news</source><target></target></trans-unit>
            </group>
        </body>
    </file>
</xliff>
'''
    target_text = r'''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
    <file original="doc.txt" source-language="en-US">
        <body>
            <trans-unit xml:space="preserve" id="header" approved="no" restype="x-gettext-domain-header">
                <source>Project-Id-Version: PACKAGE VERSION
Report-Msgid-Bugs-To:
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
X-Generator: Pootle Tests
</source>
                <target state="translated">Project-Id-Version: PACKAGE VERSION
Report-Msgid-Bugs-To:
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
X-Generator: Pootle Tests
</target>
            </trans-unit>
            <trans-unit id="Exact" approved="yes"><source>Exact</source><target>Belzabt</target></trans-unit>
            <trans-unit id="fuzzy" approved="yes"><source>fuzzy</source><target>ta2riban</target></trans-unit>
            <trans-unit id="obsolete" approved="yes"><source>obsolete</source><target>2adim</target></trans-unit>
        </body>
    </file>
</xliff>
'''
    ext = 'xlf'
    unit_count = 3
    nontrans_count = 1

    def _setup_test_files(self):
        gnu = os.path.join(self.testpodir, "testproj")
        os.mkdir(gnu)
        potfile = file(os.path.join(gnu, "test_en."+self.ext), 'w')
        potfile.write(self.template_text)
        potfile.close()
        pofile = file(os.path.join(gnu, "test_ar."+self.ext), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnu, "test_af."+self.ext), 'w')
        pofile.write(self.target_text)
        pofile.close()
        pofile = file(os.path.join(gnu, "test_zu."+self.ext), 'w')
        pofile.write(self.target_text)
        pofile.close()

    def setUp(self):
        super(XliffTests, self).setUp()
        en = require_english()
        Project.objects.get_or_create(code="testproj", fullname=u"testproj",
                                      localfiletype=self.ext, source_language=en)
        self.project = Project.objects.get(code='testproj')
        for tp in self.project.translationproject_set.iterator():
            tp.require_units()

    def test_new(self):
        """test initializing a new file from templates"""
        fr = Language.objects.get(code='fr')
        new_tp = self.project.translationproject_set.create(language=fr)
        new_tp.update_against_templates()
        store_count = new_tp.stores.count()
        self.assertEqual(store_count, 1)
        store = new_tp.stores.all()[0]
        dbunit_count = store.units.count()
        self.assertEqual(dbunit_count, self.unit_count)
        stunit_count = len(store.file.store.units)
        self.assertEqual(stunit_count, self.unit_count + self.nontrans_count)

        unit = store.findunit('%d new')
        self.assertTrue(unit)

    def test_plural(self):
        store = Store.objects.get(pootle_path='/en/testproj/test_en.'+self.ext)
        unit = store.findunit('%d new')
        self.assertTrue(unit.hasplural())

    def test_update(self):
        """test updating existing files to templates"""
        tp = self.project.translationproject_set.get(language__code='ar')
        tp.update_against_templates()

        store_count = tp.stores.count()
        self.assertEqual(store_count, 1)

        store = tp.stores.all()[0]
        dbunit_count = store.units.count()
        self.assertEqual(dbunit_count, self.unit_count)

        stunit_count = len(store.file.store.units)
        self.assertEqual(stunit_count, self.unit_count + self.nontrans_count)

        unit = store.findunit('Exact')
        self.assertEqual(unit.target, u'Belzabt')
        self.assertFalse(unit.isfuzzy())

        unit = store.findunit('Fuzzy')
        #sugg_count = unit.get_suggestions().count()
        #self.assertEqual(sugg_count, 1)
        #sugg = unit.get_suggestions()[0]
        #self.assertEqual(sugg.target, u'ta2riban')
        self.assertEqual(unit.target, u'ta2riban')
        self.assertTrue(unit.isfuzzy())

        unit = store.findunit('%d new')
        self.assertFalse(unit.istranslated())

        obsolete_count = store.unit_set.filter(state=OBSOLETE).count()
        self.assertEqual(obsolete_count, 1)
        unit = store.unit_set.filter(state=OBSOLETE)[0]
        self.assertEqual(unit.source, u'obsolete')
        self.assertEqual(unit.target, u'2adim')

        pofile = open(store.abs_real_path, 'w')
        pofile.write(self.target_text)
        pofile.close()

        store.update(update_structure=True, update_translation=True)
        unit = store.findunit('obsolete')
        self.assertEqual(unit.target, u'2adim')
        self.assertFalse(unit.isobsolete())

class CsvTests(XliffTests):
    """Tests for CSV projects"""
    template_text = r'''id, source, target, location, fuzzy
"Exact", "Exact", "", "fish.c:1", "False"
"Fuzzy", "Fuzzy", "", "test.c:1", "False"
"%d new", "%d new", "", "fish.c:2", "False"
'''
    target_text = r'''id, source, target, location, fuzzy
"Exact", "Exact", "Belzabt", "fish.c:1", "False"
"fuzzy", "fuzzy", "ta2riban", "test.c:1", "False"
"obsolete", "obsolete", "2adim", "fish.c:2", "False"
'''
    ext = 'csv'
    nontrans_count = 0

    def test_plural(self):
        # csv files don't do plurals, suppress
        pass

class TsTests(XliffTests):
    """Tests for Qt ts projects"""
    template_text = r'''<!DOCTYPE TS>
<TS version="2.0">
    <context>
        <name>header</name>
        <message><source></source><translatorcomment>some headers</translatorcomment></message>
    </context>
    <context>
        <name>fish.c</name>
        <message><source>Exact</source><translation></translation></message>
        <message><source>Fuzzy</source><translation></translation></message>
        <message numerus="yes"><source>%d new</source>
        <translation><numerusform></numerusform><numerusform></numerusform></translation></message>
    </context>
</TS>
'''
    target_text = r'''<!DOCTYPE TS>
<TS version="2.0">
    <context>
        <name>header</name>
        <message><source></source><translation>some headers</translation></message>
    </context>
    <context>
        <name>fish.c</name>
        <message><source>Exact</source><translation>Belzabt</translation></message>
        <message><source>fuzzy</source><translation>ta2riban</translation></message>
        <message><source>obsolete</source><translation>2adim</translation></message>
    </context>
</TS>
'''
    ext = 'ts'

class PropTests(XliffTests):
    """tests for java properties projects"""

    template_text = r'''# old template

Exact=Exact
fuzzy=fuzzy
obsolete=obsolete
'''
    target_text = r'''# target

Exact=Belzabt
fuzzy=ta2riban
obsolete=2adim
'''

    new_template_text = r'''# new template

Exact=Exact
Fuzzy=Fuzzy
new=%d new
'''
    ext = 'properties'

    def setUp(self):
        super(PropTests, self).setUp()
        potfile = file(os.path.join(self.testpodir, "testproj", "test_en."+self.ext), 'w')
        potfile.write(self.new_template_text)
        potfile.close()
        template_tp = self.project.translationproject_set.get(language__code='en')
        template_tp.update()

    def test_plural(self):
        # monolingual files don't do plurals, suppress
        pass

class SrtTests(PropTests):
    """Tests for subtitles projects"""

    template_text = r'''1
00:00:00,000 --> 00:00:05,000
Exact

2
00:00:06,000 --> 00:00:11,000
fuzzy

3
00:00:11,000 --> 00:00:14,000
obsolete

'''
    target_text = r'''1
00:00:00,000 --> 00:00:05,000
Belzabt

2
00:00:06,000 --> 00:00:11,000
ta2riban

3
00:00:11,000 --> 00:00:14,000
2adim
'''
    new_template_text = r'''1
00:00:00,000 --> 00:00:05,000
Exact

2
00:00:05,000 --> 00:00:11,000
Fuzzy

3
00:00:10,000 --> 00:00:14,000
%d new
'''
    ext = 'srt'
    nontrans_count = 0
