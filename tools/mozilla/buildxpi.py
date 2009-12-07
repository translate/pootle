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

"""Create a XPI language pack from Mozilla sources and translated l10n files. This script has
only been tested with Firefox 3.1 beta sources.

(Basically the process described at https://developer.mozilla.org/en/Creating_a_Language_Pack)

Example usage: buildxpi.py -L /path/to/l10n -s /path/to/mozilla-central -o /path/to/xpi_output af

- "/path/to/l10n" is the path to a the parent directory of the "af" directory containing the
  Afrikaans translated files.
- "/path/to/mozilla-central" is the path to the Firefox sources checked out from Mercurial. Note
  that --mozproduct is not specified, because the default is "browser". For Thunderbird (>=3.0) it
  should be "/path/to/comm-central" and "--mozproduct mail" should be specified, although this is
  not yet working.
- "/path/to/xpi_output" is the path to the output directory.
- "af" is the language (Afrikaans in this case) to build a language pack for.

NOTE: The .mozconfig in the process owner's home directory gets backed up, overwritten and replaced."""

import os
from glob       import glob
from shutil     import move, rmtree
from subprocess import Popen, PIPE
from tempfile   import mkdtemp


HOMEDIR = os.getenv('HOME', '~')
MOZCONFIG = os.path.join(HOMEDIR, '.mozconfig')

def run(cmd, expected_status=0, stdout=None, stderr=None, shell=False):
    if VERBOSE:
        print '>>> %s $ %s' % (os.getcwd(), ' '.join(cmd))
    p = Popen(cmd, stdout=stdout, stderr=stderr, shell=shell)
    cmd_status = p.wait()

    if stdout == PIPE:
        print p.stdout.read()
    elif stderr == PIPE:
        print p.stderr.read()

    if cmd_status != expected_status:
        print '!!! "%s" returned unexpected status %d' % (' '.join(cmd), cmd_status)
    return cmd_status

def build_xpi(l10nbase, srcdir, outputdir, lang, product, delete_dest=False):
    # Backup existing .mozconfig if it exists
    backup_name = ''
    if os.path.exists(MOZCONFIG):
        backup_name = MOZCONFIG + '.tmp'
        os.rename(MOZCONFIG, backup_name)

    # Create a temporary directory for building
    builddir = mkdtemp('', 'buildxpi')

    try:
        # Create new .mozconfig
        content = """
ac_add_options --disable-compile-environment
ac_add_options --disable-ogg
mk_add_options MOZ_OBJDIR=%(builddir)s
ac_add_options --with-l10n-base=%(l10nbase)s
ac_add_options --enable-application=%(product)s""" % \
            {
                'builddir': builddir,
                'l10nbase': l10nbase,
                'product':  product
            }

        mozconf = open(MOZCONFIG, 'w').write(content)

        # Start building process. See https://developer.mozilla.org/en/Creating_a_Language_Pack for more details.
        olddir = os.getcwd()
        os.chdir(srcdir)
        if run(['make', '-f', 'client.mk', 'configure']):
            raise Exception('^^ Fix the errors above and try again.')

        os.chdir(os.path.join(builddir, product, 'locales'))
        if run(['make', 'langpack-%s' % (lang)]):
            raise Exception('Unable to successfully build XPI!')

        xpiglob = glob(
            os.path.join(
                builddir,
                product == 'mail' and 'mozilla' or '',
                'dist',
                'install',
                '*.%s.langpack.xpi' % lang
            )
        )[0]
        if delete_dest:
            filename = os.path.split(xpiglob)[1]
            destfile = os.path.join(outputdir, filename)
            if os.path.isfile(destfile):
                os.unlink(destfile)
        move(xpiglob, outputdir)

        os.chdir(olddir)

    finally:
        # Clean-up
        rmtree(builddir)
        if backup_name:
            os.remove(MOZCONFIG)
            os.rename(backup_name, MOZCONFIG)



def create_option_parser():
    from optparse import OptionParser
    usage = 'Usage: buildxpi.py [<options>] <lang>'
    p = OptionParser(usage=usage)

    p.add_option(
        '-L', '--l10n-base',
        dest='l10nbase',
        default='l10n',
        help='The directory containing the <lang> subdirectory.'
    )
    p.add_option(
        '-o', '--output-dir',
        dest='outputdir',
        default='.',
        help='The directory to copy the built XPI to (default: current directory).'
    )
    p.add_option(
        '-p', '--mozproduct',
        dest='mozproduct',
        default='browser',
        help='The Mozilla product name (default: "browser").'
    )
    p.add_option(
        '-s', '--src',
        dest='srcdir',
        default='mozilla',
        help='The directory containing the Mozilla l10n sources.'
    )
    p.add_option(
        '-d', '--delete-dest',
        dest='delete_dest',
        action='store_true',
        default=False,
        help='Delete output XPI if it already exists.'
    )

    p.add_option(
        '-v', '--verbose',
        dest='verbose',
        action='store_true',
        default=False,
        help='Be more noisy'
    )

    return p

if __name__ == '__main__':
    options, args = create_option_parser().parse_args()

    if len(args) < 1:
        raise ArgumentError('You need to specify at least a language!')

    VERBOSE = options.verbose

    build_xpi(
        l10nbase=os.path.abspath(options.l10nbase),
        srcdir=os.path.abspath(options.srcdir),
        outputdir=os.path.abspath(options.outputdir),
        lang=args[0],
        product=options.mozproduct,
        delete_dest=options.delete_dest
    )
