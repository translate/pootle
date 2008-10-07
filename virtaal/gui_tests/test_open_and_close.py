#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Virtaal.
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

from dogtail import predicate
from time import sleep
from os import path

import common


def create_ini_file(filename):
    return common.write_file(filename, """
[translator]
email = 
name = 
team = 

[undo]
depth = 50

[language]
uilang = af_ZA
contentlang = af_ZA
sourcelang = en

[general]
windowheight = 620
windowwidth = 400""")

def handle_popup_query(node, dialog_title, input_text):
    wnd = node.child(name=dialog_title)
    box = wnd.textentry(textEntryName="")
    box.typeText(input_text)
    ok_button = wnd.button(buttonName="OK")
    ok_button.click()


class TestOpenAndClose(common.LoadSaveTest):
    def create_po_file(self, filename):
        return common.write_file(filename, """
#, fuzzy
msgid "Hello, world!"
msgstr "Hello, wereld!"
""")

    def create_pot_file(self, filename):
        return common.write_file(filename, """
msgid "Hello, world!"
msgstr ""
""")

    def after_open(self, virtaal):
        edit_area = virtaal.child(roleName='table cell')
        sleep(1)
        edit_area.keyCombo("<Alt>u")
        edit_area.typeText("Hello, wereld!")

    def after_save(self, virtaal):
        handle_popup_query(virtaal, "Please enter your name", "Hello Person")
        handle_popup_query(virtaal, "Please enter your e-mail address", "hello@world.com")
        handle_popup_query(virtaal, "Please enter your team's information", "Hello Team")

    def test_open_and_close(self):
        self.load_save_test(create_ini_file(self.abspath("config.ini")),
                            self.create_pot_file(self.abspath("hello_world.pot")),
                            self.create_po_file(self.abspath("hello_world.po")))

class TestOpenAndClose2(common.LoadSaveTest):
    def create_po_file(self, filename):
        return common.write_file(filename, """
msgid "Test 1"
msgstr "Toets 1"

msgid "Test 2"
msgstr "Toets 2"

#, fuzzy
msgid "Test 3"
msgstr "Toets 3"
""")

    def create_pot_file(self, filename):
        return common.write_file(filename, """
msgid "Test 1"
msgstr ""

msgid "Test 2"
msgstr ""

msgid "Test 3"
msgstr ""
""")

    def after_open(self, virtaal):
        cells = virtaal.findChildren(predicate.GenericPredicate(roleName="table cell"))

        cells[0].typeText("Toets 1")
        sleep(1)
        cells[0].keyCombo("Return")
        sleep(1)
        cells[1].typeText("Toets 2")
        sleep(1)
        cells[1].keyCombo("Return")
        sleep(1)
        cells[2].typeText("Toets 3")
        sleep(1)
        cells[2].keyCombo("<Alt>u")

    def test_open_and_close(self):
        self.load_save_test(common.standard_ini_file(self.abspath("config.ini")),
                            self.create_po_file(self.abspath("three_strings.pot")),
                            self.create_po_file(self.abspath("three_strings.po")))

class TestReload(common.BaseGuiTest):
    def test_reload(self):
        po_file = common.write_file(self.abspath("test.po"), """
msgid "I like jam and cheese"
msgstr "Ek hou van konfyt en kaas"
""")
        virtaal = self.run(config=common.standard_ini_file(self.abspath("config.ini")))
        common.gui_openfile(virtaal, po_file)
        common.gui_openfile(virtaal, po_file)
        virtaal.child(roleName="alert").child(roleName="push button", name="Yes").click()
        common.gui_quit(virtaal)
