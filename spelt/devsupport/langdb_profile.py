#!/usr/bin/env python

import logging

from spelt.models import LanguageDB, Source

def log(verbose, logstr):
    if verbose:
        print logstr

def test_langdb(options):
    inputdb  = options.ilangdb
    outputdb = options.olangdb
    loadonly = options.loadonly
    verbose  = options.verbose
    wordfile = options.wordfile

    log(verbose, '=== START ===')
    log(verbose, '* Loading DB: %s' % (inputdb))
    ldb = LanguageDB(filename=inputdb)
    log(verbose, '  Done')

    if loadonly:
        log(verbose, '=== END ===')
        return

    log(verbose, '* Importing word list: %s' % (wordfile))
    ldb.import_source(Source(filename=wordfile, import_user_id=2))
    log(verbose, '  Done')

    log(verbose, '* Saving %s: %s' % (ldb, outputdb))
    ldb.save(filename=outputdb)
    log(verbose, '  Done.')

    log(verbose, '=== END ===')


def create_option_parser():
    from optparse import OptionParser

    usage = '%prog [<options>]'
    parser = OptionParser(usage=usage)

    parser.add_option(
        '-v', '--verbose',
        dest='verbose',
        action='store_true',
        default=False,
        help='Print progress to STDOUT.'
    )
    parser.add_option(
        '-p', '--profile',
        dest='profilefile',
        default='langdb.profile.out',
        help='The filename to write profile data to.'
    )

    parser.add_option(
        '-i', '--inputdb',
        dest='ilangdb',
        default='testdb.xldb',
        help='The input language database to use.'
    )
    parser.add_option(
        '-o', '--outputdb',
        dest='olangdb',
        default='testdb_saved.xldb',
        help='The filename to save the output database to. Not used if -l is given.'
    )
    parser.add_option(
        '-l', '--load-only',
        dest='loadonly',
        action='store_true',
        default=False,
        help='Only load database.'
    )
    parser.add_option(
        '-w', '--wordfile',
        dest='wordfile',
        default='10k.txt',
        help='The word list file to import.'
    )

    return parser

def main():
    options, args = create_option_parser().parse_args()

    import cProfile
    import lsprofcalltree

    profiler = cProfile.Profile()
    profile_file = open(options.profilefile, 'wb')

    try:
        profiler.runcall(test_langdb, options)
    finally:
        k_cache_grind = lsprofcalltree.KCacheGrind(profiler)
        k_cache_grind.output(profile_file)

        profile_file.close()

if __name__ == '__main__':
    main()
