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


from setuptools import setup, find_packages
from distutils.core import Distribution, Command
import glob
import os
import os.path as path
import sys

import syspath_override
from pootle.__version__ import sver as pootle_version
try:
    import py2exe
    build_exe = py2exe.build_exe.py2exe
    Distribution = py2exe.Distribution
except ImportError:
    py2exe = None
    build_exe = Command

try:
    import py2app
except ImportError:
    py2app = None

PRETTY_NAME = "Pootle"
SOURCE_DATA_DIRS = ['html', 'templates']
SOURCE_DATA_DIR = "share"
SOURCE_WORKING_DIRS = ['po', 'dbs']
TARGET_WORKING_DIR = path.join("var", "lib", "Pootle")
TARGET_DATA_DIR = path.join("share", "Pootle")

pootle_description="An online collaborative localization tool."

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "Intended Audience :: End Users/Desktop",
    "Intended Audience :: Information Technology",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Programming Language :: Python",
    "Topic :: Software Development :: Localization",
    "Topic :: Text Processing :: Linguistic"
    "Operating System :: OS Independent",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: Unix"
]
#TODO: add Natural Language classifiers


def generate_data_files(roots, target_dir):
    result = []
    for root in roots:
        for path, dirs, files in os.walk(root):
            datafiles = []
            for file in files:
                datafiles.append(os.path.join(path, file))
            result.append((os.path.join(target_dir, path),  datafiles))
        
    return result


# Some of these depend on some files to be built externally before running
# setup.py, like the .xml and .desktop files
options = {
    'data_files': generate_data_files(SOURCE_DATA_DIRS, TARGET_DATA_DIR) +\
                  generate_data_files(SOURCE_WORKING_DIRS, TARGET_WORKING_DIR),
    'scripts': [
        "pootle/tools/updatetm",
        "PootleServer",
    ],
    'packages': ["pootle"] + \
                        find_packages("local_apps") + find_packages("external_apps") + \
                        ["pootle." + package for package in find_packages("pootle")],
    'package_dir': {'pootle_app': path.join('local_apps', 'pootle_app'),
                    'pootle_store': path.join('local_apps', 'pootle_store'),
                    'pootle_misc': path.join('local_apps', 'pootle_misc'),
                    'registration': path.join('external_apps', 'registration'),
                    'profiles': path.join('external_apps', 'profiles'),
                    'djblets': path.join('external_apps', 'djblets'),
                    },
}

# # For innosetup and py2app, we need to treat the plug-ins as data files.
# if os.name == 'nt' or sys.platform == 'darwin':
#     noplugins = []
#     for pkg in options['packages']:
#         if 'plugins' not in pkg:
#             noplugins.append(pkg)
#     options['packages'] = noplugins

#     plugin_src = path.join('pootle', 'plugins')
#     plugin_dest = 'pootle_plugins'
#     options['data_files'] += [
#         (plugin_dest, glob.glob(path.join(plugin_src, '*.py'))),
#         (path.join(plugin_dest, 'terminology'), glob.glob(path.join(plugin_src, 'terminology', '*.py'))),
#         (path.join(plugin_dest, 'terminology', 'models'), glob.glob(path.join(plugin_src, 'terminology', 'models', '*.py'))),
#         (path.join(plugin_dest, 'terminology', 'models', 'localfile'), glob.glob(path.join(plugin_src, 'terminology', 'models', 'localfile', '*.py'))),
#         (path.join(plugin_dest, 'tm'), glob.glob(path.join(plugin_src, 'tm', '*.py'))),
#         (path.join(plugin_dest, 'tm', 'models'), glob.glob(path.join(plugin_src, 'tm', 'models', '*.py'))),
#     ]

no_install_files = [
#    ['LICENSE', 'maketranslations', path.join('devsupport', 'pootle_innosetup.bmp')]
]

no_install_dirs = []

#############################
# WIN 32 specifics

def get_compile_command():
    try:
        import _winreg
        compile_key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, "innosetupscriptfile\\shell\\compile\\command")
        compilecommand = _winreg.QueryValue(compile_key, "")
        compile_key.Close()

    except:
        compilecommand = "compil32.exe"
    return compilecommand

def chop(dist_dir, pathname):
    """returns the path relative to dist_dir"""
    assert pathname.startswith(dist_dir)
    return pathname[len(dist_dir):]

def create_inno_script(name, _lib_dir, dist_dir, exe_files, other_files, version = "1.0"):
    if not dist_dir.endswith(os.sep):
        dist_dir += os.sep
    exe_files = [chop(dist_dir, p) for p in exe_files]
    other_files = [chop(dist_dir, p) for p in other_files]
    pathname = path.join(dist_dir, name + os.extsep + "iss")

# See http://www.jrsoftware.org/isfaq.php for more InnoSetup config options.
    ofi = open(pathname, "w")
    print >> ofi, r'''; WARNING: This script has been created by py2exe. Changes to this script
; will be overwritten the next time py2exe is run!

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "eu"; MessagesFile: "compiler:Languages\Basque.isl"
Name: "ca"; MessagesFile: "compiler:Languages\Catalan.isl"
Name: "cz"; MessagesFile: "compiler:Languages\Czech.isl"
Name: "da"; MessagesFile: "compiler:Languages\Danish.isl"
Name: "nl"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "fi"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "he"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "hu"; MessagesFile: "compiler:Languages\Hungarian.isl"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "nb"; MessagesFile: "compiler:Languages\Norwegian.isl"
Name: "pl"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "pt_BR"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "pt"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "sk"; MessagesFile: "compiler:Languages\Slovak.isl"
Name: "sl"; MessagesFile: "compiler:Languages\Slovenian.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Setup]
AppName=%(name)s
AppVerName=%(name)s %(version)s
AppPublisher=Zuza Software Foundation
AppPublisherURL=http://www.translate.org.za/
AppVersion=%(version)s
AppSupportURL=http://translate.sourceforge.net/
;AppComments=
;AppCopyright=Copyright (C) 2007-2008 Zuza Software Foundation
DefaultDirName={pf}\%(name)s
DefaultGroupName=%(name)s
OutputBaseFilename=%(name)s-%(version)s-setup
ChangesAssociations=yes
SetupIconFile=%(icon_path)s
;WizardSmallImageFile=compiler:images\WizModernSmallImage13.bmp
WizardImageFile=%(wizard_image)s

[Files]''' % {
    'name': name,
    'version': version,
    'icon_path': path.join(TARGET_DATA_DIR, "icons", "pootle.ico"),
    'wizard_image': path.join(os.pardir, "devsupport", "pootle_innosetup.bmp")
}
    for fpath in exe_files + other_files:
        print >> ofi, r'Source: "%s"; DestDir: "{app}\%s"; Flags: ignoreversion' % (fpath, os.path.dirname(fpath))
    print >> ofi, r'''
[Icons]
Name: "{group}\%(name)s Translation Editor"; Filename: "{app}\pootle.exe";
Name: "{group}\%(name)s (uninstall)"; Filename: "{uninstallexe}"''' % {'name': name}

#    For now we don't worry about install scripts
#    if install_scripts:
#        print >> ofi, r"[Run]"
#
#        for fpath in install_scripts:
#            print >> ofi, r'Filename: "{app}\%s"; WorkingDir: "{app}"; Parameters: "-install"' % fpath
#
#        print >> ofi
#        print >> ofi, r"[UninstallRun]"
#
#        for fpath in install_scripts:
#            print >> ofi, r'Filename: "{app}\%s"; WorkingDir: "{app}"; Parameters: "-remove"' % fpath

    # File associations. Note the directive "ChangesAssociations=yes" above
    # that causes the installer to tell Explorer to refresh associations.
    # This part might cause the created installer to need administrative
    # privileges. An alternative might be to rather write to
    # HKCU\Software\Classes, but this won't be system usable then. Didn't
    # see a way to test and alter the behaviour.

    # For each file type we should have something like this:
    #
    #;File extension:
    #Root: HKCR; Subkey: ".po"; ValueType: string; ValueName: ""; ValueData: "pootle_po"; Flags: uninsdeletevalue
    #;Description of the file type
    #Root: HKCR; Subkey: "pootle_po"; ValueType: string; ValueName: ""; ValueData: "Gettext PO"; Flags: uninsdeletekey
    #;Icon to use in Explorer
    #Root: HKCR; Subkey: "pootle_po\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\share\icons\pootle.ico"
    #;The command to open the file
    #Root: HKCR; Subkey: "pootle_po\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\pootle.exe"" ""%1"""

    print >> ofi, "[Registry]"
    from translate.storage import factory
    for description, extentions, _mimetypes in factory.supported_files():
        # We skip those types where we depend on mime types, not extentions
        if not extentions:
            continue
        # Form a key from the first extention for internal only
        key = extentions[0]
        # Associate each extention with the file type
        for extention in extentions:
            # We don't want to associate with all .txt or .pot (PowerPoint template) files, so let's skip it
            if extention in ["txt", "pot", "csv"]:
                continue
            print >> ofi, r'Root: HKCR; Subkey: ".%(extention)s"; ValueType: string; ValueName: ""; ValueData: "pootle_%(key)s"; Flags: uninsdeletevalue' % {'extention': extention, 'key': key}
        print >> ofi, r'''Root: HKCR; Subkey: "pootle_%(key)s"; ValueType: string; ValueName: ""; ValueData: "%(description)s"; Flags: uninsdeletekey
Root: HKCR; Subkey: "pootle_%(key)s\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\share\icons\x-translation.ico"
Root: HKCR; Subkey: "pootle_%(key)s\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\pootle.exe"" ""%%1"""''' % {'key': key, 'description': description}

    # Show a "Launch Virtaal" checkbox on the last installer screen
    print >> ofi, r'''
[Run]
Filename: "{app}\pootle.exe"; Description: "{cm:LaunchProgram,%(name)s}"; Flags: nowait postinstall skipifsilent''' % {'name': name}
    print >> ofi
    ofi.close()
    return pathname

def compile_inno_script(script_path):
    """compiles the script using InnoSetup"""
    shell_compile_command = get_compile_command()
    compile_command = shell_compile_command.replace('"%1"', script_path)
    result = os.system(compile_command)
    if result:
        print "Error compiling iss file"
        print "Opening iss file, use InnoSetup GUI to compile manually"
        os.startfile(script_path)

class BuildWin32Installer(build_exe):
    """distutils class that first builds the exe file(s), then creates a Windows installer using InnoSetup"""
    description = "create an executable installer for MS Windows using InnoSetup and py2exe"
    user_options = getattr(build_exe, 'user_options', []) + \
        [('install-script=', None,
          "basename of installation script to be run after installation or before deinstallation")]

    def initialize_options(self):
        build_exe.initialize_options(self)

    def run(self):
        # First, let py2exe do it's work.
        build_exe.run(self)
        # create the Installer, using the files py2exe has created.
        exe_files = self.windows_exe_files + self.console_exe_files
        print "*** creating the inno setup script***"
        script_path = create_inno_script(PRETTY_NAME, self.lib_dir, self.dist_dir, exe_files, self.lib_files,
                                         version=self.distribution.metadata.version)
        print "*** compiling the inno setup script***"
        compile_inno_script(script_path)
        # Note: By default the final setup.exe will be in an Output subdirectory.

def find_gtk_bin_directory():
    GTK_NAME = "libgtk"
    # Look for GTK in the user's Path as well as in some familiar locations
    paths = os.environ['Path'].split(';') + [r'C:\GTK\bin', r'C:\Program Files\GTK\bin' r'C:\Program Files\GTK2-Runtime']
    for p in paths:
        if not os.path.exists(p):
            continue
        files = [path.join(p, f) for f in os.listdir(p) if path.isfile(path.join(p, f)) and f.startswith(GTK_NAME)]
        if len(files) > 0:
            return p
    raise Exception("""Could not find the GTK runtime.
Please place bin directory of your GTK installation in the program path.""")

def find_gtk_files():
    def parent(dir_path):
        return path.abspath(path.join(path.abspath(dir_path), '..'))

    def strip_leading_path(leadingPath, p):
        return p[len(leadingPath) + 1:]

    data_files = []
    gtk_path = parent(find_gtk_bin_directory())
    for dir_path in [path.join(gtk_path, p) for p in ('etc', 'share', 'lib')]:
        for dir_name, _, files in os.walk(dir_path):
            files = [path.abspath(path.join(dir_name, f)) for f in files]
            if len(files) > 0:
                data_files.append((strip_leading_path(gtk_path, dir_name), files))
    return data_files

def add_win32_options(options):
    """This function is responsible for finding data files and setting options necessary
    to build executables and installers under Windows.

    @return: A 2-tuple (data_files, options), where data_files is a list of Windows
             specific data files (this would include the GTK binaries) and where
             options are the options required by py2exe."""
    if py2exe != None and ('py2exe' in sys.argv or 'innosetup' in sys.argv):
        options['data_files'].extend(find_gtk_files())
        #This depends on setup.py being run from a checkout with the translate
        #toolkit in place.
        options['scripts'].append("../translate/services/tmserver")

        py2exe_options = {
            "packages":   ["encodings", "translate.lang", "pootle"],
            "compressed": True,
            "excludes":   ["PyLucene", "Tkconstants", "Tkinter", "tcl", "translate.misc._csv"],
            "dist_dir":   "pootle-win32",
            "includes":   [
                    "lxml", "lxml._elementpath", "psyco", "cairo", "pango",
                    "pangocairo", "atk", "gobject", "gtk.keysyms",
                    "translate.services", "translate.storage.placeables.terminology"
                ],
            "optimize":   2,
        }
        py2exe_options['includes'] += ["bsddb", "zipfile"] # Dependencies for the migration and auto-correction plug-ins, respectively.
        innosetup_options = py2exe_options.copy()
        options.update({
            "windows": [
                {
                    'script': 'bin/pootle',
                    'icon_resources': [(1, path.join(SOURCE_DATA_DIR, "icons", "pootle.ico"))],
                },
                { 'script': "../translate/services/tmserver"}
            ],
            'zipfile':  "pootle.zip",
            "options": {
                "py2exe":    py2exe_options,
                "innosetup": innosetup_options
            },
            'cmdclass':  {
                "py2exe":    build_exe,
                "innosetup": BuildWin32Installer
            }
        })
    return options

def add_mac_options(options):
    # http://svn.pythonmac.org/py2app/py2app/trunk/doc/index.html#tweaking-your-info-plist
    # http://developer.apple.com/documentation/MacOSX/Conceptual/BPRuntimeConfig/Articles/PListKeys.html
    if py2app is None:
        return options
    options['data_files'].extend([('share/OSX_Leopard_theme', glob.glob(path.join('devsupport', 'OSX_Leopard_theme', '*')))])
    options['data_files'].extend([('', ['devsupport/pootle.icns'])])

    # For some reason py2app can't handle bin/pootle since it doesn't end in .py
    import shutil
    shutil.copy2('bin/pootle', 'bin/run_pootle.py')

    from translate.storage import factory
    options.update({
        "app": ["bin/run_pootle.py"],
        "options": {
            "py2app": {
            "packages": ["CoreFoundation", "objc"],
            "includes":   ["lxml", "lxml._elementpath", "lxml.etree", "glib", "gio", "psyco", "cairo", "pango", "pangocairo", "atk", "gobject", "gtk.keysyms", "pycurl", "translate.services", "translate.services.tmclient", "translate.services.opentranclient", "CoreFoundation"],
                #"semi_standalone": True,
                "compressed": True,
                "argv_emulation": True,
                "plist":  {
                    "CFBundleGetInfoString": pootle_description,
                    "CFBundleName": PRETTY_NAME,
                    "CFBundleIconFile": "pootle.icns",
                    "CFBundleShortVersionString": pootle_version,
                    #"LSHasLocalizedDisplayName": "1",
                    #"LSMinimumSystemVersion": ???,
                    "NSHumanReadableCopyright": "Copyright (C) 2007-2009 Zuza Software Foundation",
                    "CFBundleDocumentTypes": [{
                        "CFBundleTypeExtensions": [extention.lstrip("*.") for extention in extentions],
                        "CFBundleTypeIconFile": "pootle.icns",
                        "CFBundleTypeMIMETypes": mimetypes,
                        "CFBundleTypeName": description, #????
                        } for description, extentions, mimetypes in factory.supported_files()]
                    }
                }
            }})
    return options

def add_freedesktop_options(options):
    options['data_files'].extend([
        (path.join(TARGET_DATA_DIR, "mime", "packages"), glob.glob(path.join(SOURCE_DATA_DIR, "mime", "packages", "*.xml"))),
        (path.join(TARGET_DATA_DIR, "applications"), glob.glob(path.join(SOURCE_DATA_DIR, "applications", "*.desktop"))),
    ])
    for dir in ("16x16", "32x32", "48x48", "64x64", "128x128", "scalable"):
        options['data_files'].extend([
            (path.join(TARGET_DATA_DIR, "icons", "hicolor", dir, "mimetypes"),
            glob.glob(path.join(SOURCE_DATA_DIR, "icons", "hicolor", dir, "mimetypes", "*.*"))),
        ])
    return options

#############################
# General functions

def add_platform_specific_options(options):
    if sys.platform == 'win32':
        return add_win32_options(options)
    if sys.platform == 'darwin':
        return add_mac_options(options)
    else:
        return add_freedesktop_options(options)

def create_manifest(data_files, extra_files, extra_dirs):
    f = open('MANIFEST.in', 'w+')
    f.write("# informational files")
    for infofile in ("README", "TODO", "ChangeLog", "COPYING", "LICENSE", "*.txt"):
        f.write("global-include %s\n" % infofile)
    for data_file_list in [d[1] for d in data_files] + extra_files:
        f.write("include %s\n" % (" ".join( data_file_list )))
    for dir in extra_dirs:
        f.write("graft %s\n" % (dir))
    f.close()

import distutils.command.install
class DepCheckInstall(distutils.command.install.install):
    def __init__(self, *args, **kwargs):
        from pootle.support import depcheck
        failed = depcheck.check_dependencies()
        if failed:
            print 'Failed dependencies: %s' % (', '.join(failed))
            exit(0)
        distutils.command.install.install.__init__(self, *args, **kwargs)

def main(options):
    #options = add_platform_specific_options(options)
    #if not 'cmdclass' in options:
    #    options['cmdclass'] = {}
    #options['cmdclass']['install'] = DepCheckInstall
    create_manifest(options['data_files'], no_install_files, no_install_dirs)
    setup(name="Pootle",
          version=pootle_version,
          license="GNU General Public License (GPL)",
          description=pootle_description,
          long_description="""Pootle is used to create program translations.

It uses the Translate Toolkit to get access to translation files and therefore
can edit a variety of files (including PO and XLIFF files).""",
          author="Translate.org.za",
          author_email="translate-devel@lists.sourceforge.net",
          url="http://translate.sourceforge.net/wiki/pootle/index",
          download_url="http://sourceforge.net/project/showfiles.php?group_id=91920&package_id=270877",
          platforms=["any"],
          classifiers=classifiers,
          **options)

if __name__ == '__main__':
    main(options)
    # For some reason, Resources/lib/python2.5/lib-dynload is not in the Python
    # path. We need to get it in, therefore this hack.
    if sys.platform == 'darwin':
        f = open('dist/pootle.app/Contents/Resources/__boot__.py', "r+")
        s = f.read()
        f.truncate(0)
        s = s.replace("base = os.environ['RESOURCEPATH']", r"""
    base = os.environ['RESOURCEPATH']
    sys.path = [os.path.join(base, "lib", "python2.5", "lib-dynload")] + sys.path
    sys.path = [os.path.join(base, "lib", "python2.5")] + sys.path
""")
        f.seek(0)
        f.write(s)
        f.close()
        # hdiutil create -imagekey zlib-level=9 -srcfolder dist/pootle.app dist/pootle.dmg
        # hdiutil create -fs HFS+ -volname "RUR-PLE" -srcfolder dist dist_mac/RUR-PLE.dmg
