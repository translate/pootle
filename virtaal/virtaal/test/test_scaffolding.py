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

import os
import tempfile
from translate.storage import factory

from virtaal.controllers import *


class TestScaffolding(object):
    def setup_class(self):
        self.main_controller = MainController()
        self.store_controller = StoreController(self.main_controller)
        self.unit_controller = UnitController(self.store_controller)

        # Load additional built-in modules
        self.undo_controller = UndoController(self.main_controller)
        self.mode_controller = ModeController(self.main_controller)

        po_contents = """# Afrikaans (af) localisation of Virtaal.
# Copyright (C) 2008 Zuza Software Foundation (Translate.org.za)
# This file is distributed under the same license as the Virtaal package.
# Dwayne Bailey <dwayne@translate.org.za>, 2008
# F Wolff <friedel@translate.org.za>, 2008
msgid ""
msgstr ""
"Project-Id-Version: Virtaal 0.1\n"
"Report-Msgid-Bugs-To: translate-devel@lists.sourceforge.net\n"
"POT-Creation-Date: 2008-10-14 15:33+0200\n"
"PO-Revision-Date: 2008-10-14 15:46+0200\n"
"Last-Translator: F Wolff <friedel@translate.org.za>\n"
"Language-Team: translate-discuss-af@lists.sourceforge.net\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
"X-Generator: Virtaal 0.2\n"

#: ../bin/virtaal:41
msgid "You must specify a directory or a translation file for --terminology"
msgstr "U moet 'n gids of vertaallêer spesifiseer vir --terminology"

#: ../bin/virtaal:46
#, c-format
msgid "%prog [options] [translation_file]"
msgstr "%prog [opsies] [vertaallêer]"

#: ../bin/virtaal:49
msgid "PROFILE"
msgstr "PROFIEL"
"""
        self.testfile = tempfile.mkstemp(suffix='.po', prefix='test_storemodel')
        os.write(self.testfile[0], po_contents)
        os.close(self.testfile[0])
        self.trans_store = factory.getobject(self.testfile[1])

    def teardown_class(self):
        os.unlink(self.testfile[1])
