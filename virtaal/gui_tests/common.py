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
from os import path, environ

from dogtail import tree, config
from dogtail.utils import run

import po2pot


environ['LANGUAGE']='en_US.UTF-8'

if environ.has_key('TEST_TURBO'):
    config.config.defaults['absoluteNodePaths'] = True
    config.config.defaults['typingDelay'] = 0.01
    config.config.defaults['actionDelay'] = 0.1
    #config.config.defaults['defaultDelay'] = 0.1
    config.config.defaults['runTimeout'] = 0.01
    config.config.defaults['searchCutoffCount'] = 2
else:
    config.config.defaults['absoluteNodePaths'] = True
    config.config.defaults['typingDelay'] = 0.02
    config.config.defaults['actionDelay'] = 0.3

def find_app(exe_name):
    full_exe_name = path.abspath(exe_name)
    full_exe_dir_name = path.dirname(full_exe_name)

    # If the parent of the current pathname is the same as the current pathname,
    # we've hit the topmost directory and we give up, returning None
    if full_exe_dir_name == path.abspath(path.join(full_exe_dir_name, "..")):
        return None

    if path.exists(full_exe_name):
        return full_exe_name
    else:
        return find_app(path.join("..", exe_name))


class BaseGuiTest(object):
    """Tests running actual commands on files"""
    defaultoptions = {}
    virtaal_cmd = "run_virtaal.py"

    def __init__(self):
        self.config_file = None
        self.testdir = None
        self.rundir = None

    def abspath(self, partial_fname):
        return path.abspath(path.join(self.testdir, partial_fname))

    def setup_method(self, method):
        """creates a clean test directory for the given method"""
        self.testdir = "%s_%s" % (self.__class__.__name__, method.__name__)
        self.cleardir()
        os.mkdir(self.testdir)
        self.rundir = os.path.abspath(os.getcwd())

    def teardown_method(self, _method):
        """removes the test directory for the given method"""
        os.chdir(self.rundir)
        self.cleardir()

    def cleardir(self):
        """removes the test directory"""
        if os.path.exists(self.testdir):
            for dirpath, subdirs, filenames in os.walk(self.testdir, topdown=False):
                for name in filenames:
                    os.remove(os.path.join(dirpath, name))
                for name in subdirs:
                    os.rmdir(os.path.join(dirpath, name))
        if os.path.exists(self.testdir): os.rmdir(self.testdir)
        assert not os.path.exists(self.testdir)

    def run(self, *argv, **kwargs):
        """runs the command via the main function, passing self.defaultoptions and keyword arguments as --long options and argv arguments straight"""
        os.chdir(self.testdir)
        argv = list(argv)
        kwoptions = getattr(self, "defaultoptions", {}).copy()
        kwoptions.update(kwargs)
        for key, value in kwoptions.iteritems():
            if value is True:
                argv.append("--%s" % key)
            else:
                argv.append("--%s=%s" % (key, value))

        cmd = "%s %s" % (find_app(self.virtaal_cmd), " ".join(argv))
        run(cmd, timeout=0)
        return self.get_app()

    def get_app(self):
        return tree.root.application(self.virtaal_cmd)


class LoadSaveTest(BaseGuiTest):
    def after_open(self, node):
        pass

    def after_save(self, node):
        pass

    def load_save_test(self, config_file, source_file, target_file, after_open=lambda x: x, after_save=lambda x: x):
        dirname, filename = path.split(target_file)
        test_target_file = path.join(dirname, "test_" + filename)
        source_file = strip_translations(self.abspath(target_file))
        virtaal = self.run(config=self.abspath(config_file))

        gui_openfile(virtaal, source_file)
        self.after_open(virtaal)
        gui_saveas(virtaal, test_target_file)
        self.after_save(virtaal)
        gui_quit(virtaal)

        contents = read_file(test_target_file).split("\n\n")
        assert "\n\n".join(contents[1:]).strip("\n") == read_file(target_file).strip("\n")


def standard_ini_file(filename):
    return write_file(filename, """
[translator]
email = hello@world.com
name = Person
team = Team

[undo]
depth = 50

[language]
uilang = af_ZA
contentlang = af_ZA
sourcelang = en

[general]
windowheight = 620
windowwidth = 400""")


def click_file_open(node):
    node.menuItem("File").menuItem("Open").click()
    return node.child(roleName="dialog")

def gui_openfile(node, filename):
    dlg = click_file_open(node)

    filename_box = dlg.child(label='Location:')
    filename_box.grabFocus()
    filename_box.keyCombo("BackSpace")
    filename_box.typeText(filename)

    ok_button = dlg.child(roleName="push button", name="Open")
    ok_button.click()

def click_file_saveas(node):
    node.menuItem("File").menuItem("Save As").click()
    return node.child(roleName="dialog")

def gui_saveas(node, filename):
    dlg = click_file_saveas(node)

    filename_box = dlg.child(label='Name:')
    filename_box.grabFocus()
    filename_box.keyCombo("<Ctrl>a")
    filename_box.keyCombo("BackSpace")
    filename_box.typeText(filename)

    save_button = dlg.button(buttonName="Save")
    save_button.click()

def gui_quit(node):
    node.menuItem("File").menuItem("Quit").click()

def test_fname(dirname, filename):
    return path.join(dirname, filename)

def ensure_dir_exists(dirname):
    if path.exists(dirname) and not path.isdir(dirname):
        os.unlink(dirname)
    if not path.exists(dirname):
        os.makedirs(dirname)

def enter_test_dir(test_name):
    ensure_dir_exists(test_name)
    os.chdir(test_name)

def write_file(filename, data):
    f = open(filename, 'w+')
    try:
        f.write(data)
        return filename
    finally:
        f.close()
    return filename

def read_file(filename):
    return open(filename).read()

def strip_translations(po_filename):
    fname, ext = path.splitext(po_filename)
    if ext != '.po':
        raise NameError("The extension should be .pot")
    pot_filename = fname + ".pot"
    po2pot.main([po_filename, pot_filename])
    return pot_filename
