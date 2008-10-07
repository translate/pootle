#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
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
#
# moz-l10n-builder - takes a set of PO files, migrates them to a Mozilla build
# and creates XPIs and Windows .exe files.

"""Contains a Python-port of the moz-l10n-builder bash script."""

# NOTE: Because this script is adapted from a Bash script, some things in here
#       might be a little less Pythonic. See os.system() calls for more
#       details.

import glob
import os
import shutil
import StringIO
import tempfile
import time
from subprocess import Popen, PIPE, STDOUT

join = os.path.join

try:
    # Make sure that all convertion tools are available
    from translate.convert import moz2po
    from translate.convert import po2moz
    from translate.convert import po2prop
    from translate.convert import txt2po
except ImportError:
    raise Exception('Could not find the Translate Toolkit convertion tools. Please check your installation.')

DEFAULT_TARGET_APP = 'browser'
langpack_release = '1'
targetapp = 'browser'
mozversion = '3'
l10ndir = 'l10n'
mozilladir = "mozilla"
podir = "po"
podir_recover = podir + '-recover'
podir_updated = podir + '-updated'
potpacks = "potpacks"
popacks = 'popacks'
products = { 'browser': 'firefox' } #Simple mapping of possible "targetapp"s to product names.

devnull = open(os.devnull, 'wb')
options = { 'verbose': True } # Global program options
USAGE='Usage: %prog [options] <langs...|ALL>'

class CommandError(StandardError):
    """Exception raised if a command does not return its expected value."""

    def __init__(self, cmd, status):
        self.cmd = cmd
        self.status = status

    def __str__(self):
        return '"%s" return unexptected status %d' % (self.cmd, self.status)

##### Utility Functions #####
def delfiles(pattern, path, files):
    """Delete files with names in C{files} matching glob-pattern C{glob} in the
        directory specified by C{path}.

        This function is meant to be used with C{os.path.walk}
        """
    path = os.path.abspath(path)
    match_files = glob.glob( join(path, pattern) )
    for f in files:
        if join(path, f) in match_files:
            os.unlink(join(path, f))

def run(cmd, expected_status=0, stdout=None, stderr=None, shell=False):
    global options
    if options['verbose']:
        print '>>> %s $ %s' % (os.getcwd(), ' '.join(cmd))
    p = Popen(cmd, stdout=stdout, stderr=stderr, shell=shell)
    cmd_status = p.wait()

    if stdout == PIPE:
        print p.stdout.read()
    elif stderr == PIPE:
        print p.stderr.read()

    if cmd_status != expected_status:
        print '!!! "%s" returned unexpected status %d' % (' '.join(cmd), cmd_status)
        #raise CommandError(cmd, cmd_status)

def get_langs(lang_args):
    """Returns the languages to handle based on the languages specified on the
        command-line.

        If "ALL" was specified, the languages are read from the Mozilla
        product's C{shipped-locales} file. If "ZA" was specified, all South
        African languages are selected.
        """

    langs = []

    if isinstance(lang_args, str):
        if lang_args == 'ALL':
            lang_args = ['ALL']
        elif lang_args == 'ZA':
            lang_args = ['ZA']
        else:
            lang_args = []

    if not lang_args:
        print USAGE
        exit(1)

    for lang in lang_args:
        if lang == 'ALL':
            # Get all available languages from the locales file
            locales_filename = join(mozilladir, targetapp, 'locales', 'shipped-locales')
            for line in open(locales_filename).readlines():
                langcode = line.split()[0]
                if langcode != 'en-US':
                    langs.append(langcode)

        elif lang == 'ZA':
            # South African languages
            langs = langs + ["af", "en_ZA", "nr", "nso", "ss", "st", "tn", "ts", "ve", "xh", "zu"]
        elif lang != 'en-US':
            langs.append(lang)

    langs = list(set(langs)) # Remove duplicates from langs

    print 'Selected languages: %s' % (' '.join(langs))

    return langs
#############################

def checkout(cvstag, langs):
    """Check-out needed files from Mozilla's CVS."""

    olddir = os.getcwd()
    if cvstag != '-A':
        cvstag = "-r %s" % (cvstag)

    if not os.path.exists(mozilladir):
        run(['cvs', '-d:pserver:anonymous@cvs-mirror.mozilla.org:/cvsroot', 'co', cvstag, join(mozilladir, 'client.mk')])
        run(['cvs', '-d:pserver:anonymous@cvs-mirror.mozilla.org:/cvsroot', 'co', join(mozilladir, 'tools', 'l10n')])

    os.chdir(mozilladir)
    run(['cvs', 'up', cvstag, 'client.mk'])
    run(['make', '-f', 'client.mk', 'l10n-checkout', 'MOZ_CO_PROJECT=%s' % (targetapp)])
    os.chdir(olddir)

    if not os.path.exists(l10ndir):
        run(['cvs', '-d:pserver:anonymous@cvs-mirror.mozilla.org:/l10n', 'co', '-d', l10ndir, '-l', 'l10n'])

    os.chdir(l10ndir)
    for lang in langs:
        print '    %s' % (lang)
        buildlang=lang.replace('_', '-')
        if os.path.isdir(buildlang):
            run(['cvs', 'up', buildlang])
        else:
            run(['cvs', '-d:pserver:anonymous@cvs-mirror.mozilla.org:/l10n', 'co', '-d', buildlang, join('l10n', buildlang)])
    os.chdir(olddir)

    # Make latest POT file
    for rmdir in ('en-US', 'pot'):
        try:
            shutil.rmtree( join(l10ndir, rmdir) )
        except OSError, oe:
            # "No such file or directory" errors are fine. The rest we raise again.
            if oe.errno != 2:
                raise oe

    os.chdir(mozilladir)
    run(['cvs', 'up', join('tools', 'l10n')])
    run(['python', 'tools/l10n/l10n.py', '--dest='+join(os.pardir, l10ndir), '--app='+targetapp, 'en-US'])
    os.chdir(olddir)

    os.chdir(l10ndir)
    run(['moz2po', '--progress=none', '-P', '--duplicates=msgctxt', 'en-US', 'pot'])

    # Delete the help-related POT-files, seeing as Firefox help is now on-line.
    try:
        shutil.rmtree(join('pot', 'browser', 'chrome', 'help'))
    except OSError, oe:
        # "No such file or directory" errors are fine. The rest we raise again.
        if oe.errno != 2:
            raise oe

    if mozversion < '3':
        for f in [  'en-US/browser/README.txt pot/browser/README.txt.pot',
                    'en-US/browser/os2/README.txt pot/browser/os2/README.txt.pot',
                    'en-US/mail/README.txt pot/mail/README.txt.pot',
                    'en-US/mail/os2/README.txt pot/mail/os2/README.txt.pot' ]:
            run(['txt2po', '--progress=none', '-P', f])
    os.chdir(olddir)

def recover_lang(lang, buildlang):
    print '    %s' % (lang)
    if not os.path.isdir(join(podir_recover, buildlang)):
        os.makedirs(join(podir_recover, buildlang))

    run(['moz2po', '--progress=none', '--errorlevel=traceback', '--duplicates=msgctxt', '--exclude=".#*"',
         '-t', join(l10ndir, 'en-US'),
         join(l10ndir, buildlang),
         join(podir_recover, buildlang)])

def pack_pot(includes):
    timestamp = time.strftime('%Y%m%d')

    inc = []
    for fn in includes:
        if not os.path.exists(fn):
            print '!!! Warning: Path "%s" does not exist. Skipped.' % (fn)
        else:
            inc.append(fn)

    try:
        os.makedirs(potpacks)
    except OSError:
        pass

    packname = join(potpacks, '%s-%s-%s' % (products[targetapp], mozversion, timestamp))
    run(['tar', 'cjf', packname+'.tar.bz2',
         join(l10ndir, 'en-US'), join(l10ndir, 'pot') ] + inc)
    run(['zip', '-qr9', packname+'.zip',
         join(l10ndir, 'en-US'), join(l10ndir, 'pot') ] + inc)

def pack_po(lang, buildlang):
    timestamp = time.strftime('%Y%m%d')

    try:
        os.makedirs(popacks)
    except OSError:
        pass

    print '    %s' % (lang)
    packname = join(popacks, '%s-%s-%s-%s' % (products[targetapp], mozversion, buildlang, timestamp))
    run(['tar', 'cjf', packname+'.tar.bz2', join(l10ndir, buildlang)])
    run(['zip', '-qr9', packname+'.zip', join(l10ndir, buildlang)])

def pre_po2moz_hacks(lang, buildlang, debug):
    """Hacks that should be run before running C{po2moz}."""

    # Protect the real original PO dir
    temp_po = tempfile.mkdtemp()
    shutil.copytree( join(podir, buildlang), join(temp_po, buildlang) )

    # Fix for languages that have no Windows codepage
    if lang == 've':
        srcs = glob.glob(join(podir, 'en_ZA', 'browser', 'installer', '*.properties'))
        dest = join(temp_po, buildlang, 'browser', 'installer')

        for src in srcs:
            shutil.copy2(src, dest)

    old = join(temp_po, buildlang)
    new = join(podir_updated, buildlang)
    templates = join(l10ndir, 'pot')
    run(['pomigrate2', '--use-compendium', '--quiet', '--pot2po', old, new, templates])

    os.path.walk(join(podir_updated, buildlang), delfiles, '*.html.po')
    os.path.walk(join(podir_updated, buildlang), delfiles, '*.xhtml.po')

    if debug:
        olddir = os.getcwd()
        os.chdir(join("%s" % (podir_updated), buildlang))
        run(['podebug', '--progress=none', '--errorlevel=traceback', '--ignore=mozilla', '.', '.'])
        os.chdir(olddir)

    # Create l10n related files
    if os.path.isdir( join(l10ndir, buildlang) ):
        os.path.walk(join(l10ndir, buildlang), delfiles, '*.dtd')
        os.path.walk(join(l10ndir, buildlang), delfiles, '*.properties')

    shutil.rmtree(temp_po)

def post_po2moz_hacks(lang, buildlang):
    """Hacks that should be run after running C{po2moz}."""

    # Hack to fix creating Thunderber installer
    inst_inc_po = join(podir_updated, lang, 'mail', 'installer', 'installer.inc.po')
    if os.path.isfile(inst_inc_po):
        tempdir = tempfile.mkdtemp()
        tmp_po = join(tempdir, 'installer.%s.properties.po' % (lang))
        shutil.copy2(inst_po, tmp_po)

        inst_inc = join(l10ndir, 'en-US', 'mail', 'installer', 'installer.inc')
        tmp_properties = join(tempdir, 'installer.properties')
        shutil.copy2(inst_inc, tmp_properties)

        run(['po2prop', '--progress=none', '--errorlevel=traceback',
             '-t', tmp_properties, # -t /tmp/installer.properties
             tmp_po,               # /tmp/installer.$lang.properties.po
             tmp_po[:-3]])           # /tmp/installer.$lang.properties

        # mv /tmp/installer.$lang.properties $l10ndir/$buildlang/mail/installer/installer.inc
        shutil.move(
            tmp_po[:-3],
            join(l10ndir, buildlang, 'mail', 'installer', 'installer.inc')
        )

        shutil.rmtree(tempdir)

    def copyfile(filename, language):
        enUS = join(l10ndir, 'en-US')
        dir, filename = os.path.split(filename)

        if dir.startswith(enUS):
            dir = dir[len(enUS)+1:]

        if os.path.isfile(join(enUS, dir, filename)):
            try:
                os.makedirs(join(l10ndir, language, dir))
            except OSError:
                pass # Don't worry if the directory already exists
            shutil.copy2(
                join(enUS, dir, filename),
                join(l10ndir, language, dir)
            )

    def copyfiletype(filetype, language):
        def checkfiles(filetype, dir, files):
            for f in files:
                if f.endswith(filetype):
                    copyfile(join(dir, f), language)

        os.path.walk(join(l10ndir, 'en-US'), checkfiles, filetype)

    # Copy and update non-translatable files
    for ft in ('.xhtml', '.html', '.rdf'):
        copyfiletype(ft, buildlang)

    for f in (
            join('browser', 'extra-jar.mn'),
            join('browser', 'firefox-l10n.js'),
            join('browser', 'README.txt'),
            join('browser', 'microsummary-generators', 'list.txt'),
            join('browser', 'profile', 'chrome', 'userChrome-example.css'),
            join('browser', 'profile', 'chrome', 'userContent-example.css'),
            join('browser', 'searchplugins', 'list.txt'),
            join('extensions', 'reporter', 'chrome', 'reporterOverlay.properties'),
            join('mail', 'all-l10n.js'),
            join('toolkit', 'chrome', 'global', 'intl.css'),
            join('toolkit', 'installer', 'windows', 'charset.mk')
        ):
        copyfile(f, buildlang)


def migrate_lang(lang, buildlang, recover, update_transl, debug):
    print '    %s' % (lang)

    if recover and not os.path.isdir(join(podir, buildlang)):
        # If we recovered the .po files for lang, but there is no other po
        # directory, we use the recovered .po files
        try:
            os.mkdir(podir)
        except OSError, oe:
            # "File exists" errors are fine. The rest we raise again.
            if oe.errno != 17:
                raise oe

        shutil.copytree(join(podir_recover, buildlang), join(podir, buildlang))

    if update_transl:
        olddir = os.getcwd()
        os.chdir(podir)
        run(['svn', 'up', buildlang])
        os.chdir(olddir)

        os.chdir(l10ndir)
        run(['cvs', 'up', buildlang])
        os.chdir(olddir)

    # Migrate language from current PO to latest POT
    if os.path.isdir(join(podir, '.svn')):
        shutil.rmtree(join(podir_updated, '.svn'))
        shutil.copytree(join(podir, '.svn'), podir_updated)
    if os.path.isdir(join(podir_updated, buildlang)):
        shutil.rmtree(join(podir_updated, buildlang))
    shutil.copytree( join(podir, buildlang), join(podir_updated, buildlang) )
    os.path.walk(join(podir_updated, buildlang), delfiles, '*.po')

    pre_po2moz_hacks(lang, buildlang, debug)

    ###################################################
    args = [
        '--progress=none',
        '--errorlevel=traceback',
        '--exclude=".svn"',
        '-t', join(l10ndir, 'en-US'),
        '-i', join(podir_updated, buildlang),
        '-o', join(l10ndir, buildlang)
    ]

    if debug:
        args.append('--fuzzy')

    run(['po2moz'] + args)
    ###################################################

    post_po2moz_hacks(lang, buildlang)

    # Clean up where we made real tabs \t
    if mozversion < '3':
        run(['sed', '-i', '"/^USAGE_MSG/s/\\\t/\t/g"',
             join(l10ndir, buildlang, 'toolkit', 'installer', 'unix', 'install.it')])
        run(['sed', '-i', '"/^#define MSG_USAGE/s/\\\t/\t/g"',
             join(l10ndir, buildlang, 'browser', 'installer', 'installer.inc')])

    # Fix bookmark file to point to the locale
    # FIXME - need some way to preserve this file if its been translated already
    run(['sed', '-i', 's/en-US/%s/g' % (buildlang),
         join(l10ndir, buildlang, 'browser', 'profile', 'bookmarks.html')])

def create_diff(lang, buildlang):
    """Create CVS-diffs for all languages."""

    if not os.path.isdir('diff'):
        os.mkdir('diff')

    print '    %s' % (lang)
    olddir = os.getcwd()

    os.chdir(l10ndir)
    outfile = join(os.pardir, 'diff', buildlang+'-l10n.diff')
    run(['cvs', 'diff', '--newfile', buildlang], stdout=open(outfile, 'w'))
    os.chdir(olddir)

    os.chdir(join(podir_updated, buildlang))
    outfile = join(os.pardir, os.pardir, 'diff', buildlang+'-po.diff')
    run(['svn', 'diff', '--diff-cmd', 'diff -x "-u --ignore-matching-lines=^\"POT\|^\"X-Gene"'], stdout=open(outfile, 'w'))
    os.chdir(olddir)

def create_langpack(lang, buildlang):
    """Builds a XPI and installers for languages."""

    print '    %s' % (lang)

    olddir = os.getcwd()

    os.chdir(mozilladir)
    run(['./configure', '--disable-compile-environment', '--disable-xft', '--enable-application=%s' % (targetapp)])
    os.chdir(olddir)

    os.chdir(join(mozilladir, targetapp, 'locales'))
    langpack_name = 'langpack-' + buildlang
    moz_brand_dir = join('other-licenses', 'branding', 'firefox')
    langpack_file = join("'$(_ABS_DIST)'", 'install', "Firefox-Languagepack-'$(MOZ_APP_VERSION)'-%s.'$(AB_CD)'.xpi" % langpack_release)
    run(['make', langpack_name, 'MOZ_BRANDING_DIRECTORY='+moz_brand_dir, 'LANGPACK_FILE='+langpack_file])
    # The commented out (and very long) line below was found commented out in the source script as well.
    #( cd $mozilladir/$targetapp/locales; make repackage-win32-installer-af MOZ_BRANDING_DIRECTORY=other-licenses/branding/firefox WIN32_INSTALLER_IN=../../../Firefox-Setup-2.0.exe WIN32_INSTALLER_OUT='$(_ABS_DIST)'"/install/sea/Firefox-Setup-"'$(MOZ_APP_VERSION).$(AB_CD)'".exe" )
    os.chdir(olddir)


def create_option_parser():
    """Creates and returns cmd-line option parser."""

    from optparse import OptionParser

    parser = OptionParser(usage=USAGE)

    parser.add_option(
        '-q', '--quiet',
        dest='verbose',
        action='store_false',
        default=True,
        help='Print as little as possible output.'
    )
    parser.add_option(
        '--mozilla-product',
        dest='mozproduct',
        default=DEFAULT_TARGET_APP,
        help='Which product to build'
    )
    parser.add_option(
        '--mozilla-checkout',
        dest='mozcheckout',
        action='store_true',
        default=False,
        help="Update of the Mozilla l10n files and POT files"
    )
    parser.add_option(
        '--recover',
        dest='recover',
        action='store_true',
        default=False,
        help="build PO files from Mozilla's l10n files"
    )
    parser.add_option(
        '--mozilla-tag',
        dest='moztag',
        default='-A',
        help='The tag to check out of CVS (implies --mozilla-checkout)'
    )
    parser.add_option(
        '--update-translations',
        dest='update_translations',
        action='store_true',
        default=False,
        help="Update translations"
    )
    parser.add_option(
        '--diff',
        dest='diff',
        action='store_true',
        default=False,
        help='Create diffs for migrated translations and localized Mozilla files'
    )
    parser.add_option(
        '--potpack',
        dest='potpack',
        action='store_true',
        default=False,
        help="Create packages of the en-US and POT directories with today's timestamp"
    )
    parser.add_option(
        '--pot-include',
        dest='potincl',
        action='append',
        default=[],
        help='Files to include in the POT pack (only used with --potpack)'
    )
    parser.add_option(
        '--nomigrate',
        dest='migrate',
        action='store_false',
        default=True,
        help="Don't migrate"
    )
    parser.add_option(
        '--popack',
        dest='popack',
        action='store_true',
        default=False,
        help="Create packages of all specified languages' PO-files with today's timestamp"
    )
    parser.add_option(
        '--langpack',
        dest='langpack',
        action='store_true',
        default=False,
        help="Build a langpack"
    )
    parser.add_option(
        '--debug',
        dest='debug',
        action='store_true',
        default=False,
        help="Add podebug debug markers"
    )

    return parser

def main(
        langs=['ALL'], mozproduct='browser', mozcheckout=False, moztag='-A',
        recover=False, potpack=False, potincl=[], migrate=True, popack=False,
        update_trans=False, debug=False, diff=False, langpack=False,
        verbose=True
        ):
    global options
    options['verbose'] = verbose
    targetapp = mozproduct
    langs = get_langs(langs)

    if mozcheckout:
        print 'Checking out'
        checkout(moztag, langs)

    if potpack:
        print 'Packing POT files'
        pack_pot(potincl)

    for lang in langs:
        buildlang = lang.replace('_', '-')

        if recover:
            print 'Recovering'
            recover_lang(lang, buildlang)

        if migrate:
            print 'Migrating'
            migrate_lang(lang, buildlang, recover, update_trans, debug)

        if popack:
            print 'Creating PO-packs'
            pack_po(lang, buildlang)

        if diff:
            print 'Creating diffs'
            create_diff(lang, buildlang)

        if langpack:
            print 'Creating langpacks'
            create_langpack(lang, buildlang)

    print 'FIN'
    devnull.close()


def main_cmd_line():
    options, args = create_option_parser().parse_args()

    main(
        langs=args,
        mozproduct=targetapp,
        mozcheckout=options.mozcheckout,
        moztag=options.moztag,
        recover=options.recover,
        potpack=options.potpack,
        potincl=options.potincl,
        migrate=options.migrate,
        popack=options.popack,
        update_trans=options.update_translations,
        debug=options.debug,
        diff=options.diff,
        langpack=options.langpack,
        verbose=options.verbose
    )

if __name__ == '__main__':
    main_cmd_line()
