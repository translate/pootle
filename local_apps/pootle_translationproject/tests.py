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

from pootle.tests import PootleTestCase

from pootle_project.models import Project
from pootle_store.models import Store
from pootle_app.project_tree import get_translated_name, get_translated_name_gnu
from pootle_language.models import Language
from pootle_store.util import OBSOLETE

class GnuTests(PootleTestCase):
    """Tests for Gnu Style projects"""

    template_text = r'''msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"Report-Msgid-Bugs-To: \n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"X-Generator: Pootle Tests\n"

#: fish.c
msgid "Exact"
msgstr ""

#: test.c
msgid "Fuzzy"
msgstr ""

#: fish.c
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

#: fish.c
msgid "Exact"
msgstr "Belzabt"

#: test.c
msgid "fuzzy"
msgstr "ta2riban"

#: fish.c
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

    def setUp(self):
        super(GnuTests, self).setUp()
        from pootle_app.management import require_english
        en = require_english()
        Project.objects.get_or_create(code="testproj", fullname=u"testproj",
                                      source_language=en)
        self.project = Project.objects.get(code='testproj')

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
        self.assertEqual(lang_count, 4)

        store_count = Store.objects.filter(translation_project__project=self.project).count()
        self.assertEqual(store_count, 4)

        lang_list = list(self.project.translationproject_set.values_list('language__code', flat=True).order_by('language__code'))
        self.assertEqual(lang_list, [u'af', u'ar', u'templates', u'zu'])

    def test_template_detection(self):
        """test that given a template the correct target file name is generated"""
        template_tp = self.project.get_template_translationproject()
        template_store = template_tp.stores.get(name='test.pot')
        for tp in self.project.translationproject_set.exclude(language__code='templates').iterator():
            new_pootle_path, new_path = get_translated_name_gnu(tp, template_store)
            store = tp.stores.all()[0]
            self.assertEqual(new_pootle_path, store.pootle_path)
            self.assertEqual(new_path, store.abs_real_path)

    def test_new(self):
        """test initializing a new file from templates"""
        fr = Language.objects.get(code='fr')
        new_tp = self.project.translationproject_set.create(language=fr)
        new_tp.update_from_templates()
        store_count = new_tp.stores.count()
        self.assertEqual(store_count, 1)
        store = new_tp.stores.all()[0]
        dbunit_count = store.units.count()
        self.assertEqual(dbunit_count, 3)
        stunit_count = len(store.file.store.units)
        self.assertEqual(stunit_count, 4)

    def test_update(self):
        """test updating existing files to templates"""
        tp = self.project.translationproject_set.get(language__code='ar')
        tp.update_from_templates()

        store_count = tp.stores.count()
        self.assertEqual(store_count, 1)

        store = tp.stores.all()[0]
        dbunit_count = store.units.count()
        self.assertEqual(dbunit_count, 3)

        stunit_count = len(store.file.store.units)
        self.assertEqual(stunit_count, 5)

        unit = store.findid('Exact')
        self.assertEqual(unit.target, u'Belzabt')
        self.assertFalse(unit.isfuzzy())

        unit = store.findid('Fuzzy')
        self.assertEqual(unit.target, u'ta2riban')
        self.assertTrue(unit.isfuzzy())

        unit = store.findid('%d new')
        self.assertFalse(unit.istranslated())

        #obsolete_count = store.unit_set.filter(state=OBSOLETE).count()
        #self.assertEqual(obsolete_count, 1)
        #unit = store.unit_set.filter(state=OBSOLETE)[0]
        #self.assertEqual(unit.source, u'obsolete')
        #self.assertEqual(unit.target, u'2adim')

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

    def test_realpath(self):
        """test that physical path is calculated correctly"""
        for tp in self.project.translationproject_set.iterator():
            expected_path = u'testproj/%s' % tp.language.code
            self.assertEqual(tp.real_path, expected_path)

    def test_template_detection(self):
        """test that given a template the correct target file name is generated"""
        template_tp = self.project.get_template_translationproject()
        template_store = template_tp.stores.get(name='test.pot')
        for tp in self.project.translationproject_set.exclude(language__code='templates').iterator():
            new_pootle_path, new_path = get_translated_name(tp, template_store)
            store = tp.stores.all()[0]
            self.assertEqual(new_pootle_path, store.pootle_path)
            self.assertEqual(new_path, store.abs_real_path)

    def test_treestyle(self):
        """test treestyle detection"""
        self.assertEqual(self.project.get_treestyle(), 'nongnu')

