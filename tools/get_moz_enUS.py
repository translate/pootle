#!/usr/bin/env python

import os
import shutil
from ConfigParser import ConfigParser, NoSectionError


srccheckout = "mozilla"
l10ncheckout = "l10n"
product = "browser"
verbose = False

def path_neutral(path):
    """Convert a path specified using Unix path seperator into a platform path"""
    newpath = ""
    for seg in path.split("/"):
        if not seg:
            newpath = os.sep
        newpath = os.path.join(newpath, seg)
    return newpath


def process_l10n_ini(inifile):
    """Read a Mozilla l10n.ini file and process it to find the localisation files
    needed by a project"""

    l10n = ConfigParser()
    l10n.readfp(open(path_neutral(inifile)))
    l10n_ini_path = os.path.dirname(inifile)

    for dir in l10n.get('compare', 'dirs').split():
        frompath = os.path.join(l10n_ini_path, l10n.get('general', 'depth'), dir, 'locales', 'en-US')
        if verbose:
            print '%s -> %s' % (frompath, os.path.join(l10ncheckout, 'en-US', dir))
        shutil.copytree(frompath, os.path.join(l10ncheckout, 'en-US', dir))

    try:
        for include in l10n.options('includes'):
            process_l10n_ini(os.path.join( l10n_ini_path, l10n.get('general', 'depth'), l10n.get('includes', include) ))
    except TypeError:
        pass
    except NoSectionError:
        pass



def create_option_parser():
    from optparse import OptionParser
    p = OptionParser()

    p.add_option(
        '-s', '--src',
        dest='srcdir',
        default='mozilla',
        help='The directory containing the Mozilla l10n sources.'
    )
    p.add_option(
        '-d', '--dest',
        dest='destdir',
        default='l10n',
        help='The destination directory to copy the en-US locale files to.'
    )
    p.add_option(
        '-p', '--mozproduct',
        dest='mozproduct',
        default='browser',
        help='The Mozilla product name.'
    )
    p.add_option(
        '--delete-dest',
        dest='deletedest',
        default=False,
        action='store_true',
        help='Delete the destination directory (if it exists).'
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
    srccheckout = options.srcdir
    l10ncheckout = options.destdir
    product = options.mozproduct
    verbose = options.verbose

    enUS_dir = os.path.join(l10ncheckout, 'en-US')
    if options.deletedest and os.path.exists(enUS_dir):
        shutil.rmtree(enUS_dir)
    if not os.path.exists(enUS_dir):
        os.makedirs(enUS_dir)

    if verbose:
        print "%s -s %s -d %s -p %s -v %s" % (__file__, srccheckout, l10ncheckout, product,
                options.deletedest and '--delete-dest' or '')
    product_ini = os.path.join(srccheckout, product, 'locales', 'l10n.ini')
    process_l10n_ini(product_ini)
