#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of CorpusCatcher.
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

import md5
import os
import random
import httplib, urlparse
from gettext   import gettext as _
from mechanize import Browser
from popen2    import popen2

from h2t import html2text

def _build_random_tuples(seeds, n=3, l=10):
    """Port of BootCaT's build_random_tuples.pl."""

    seeds = [seed.replace('\r', '').replace('\n', '') for seed in seeds]

    def factorial(n):
        if n < 0:
            return None
        if n == 0:
            return 1
        return n * factorial(n-1)

    k = len(seeds)
    combs = factorial(k) / (factorial(k - n) * factorial(n)) # number of possible combinations of seeds

    if l > combs:
        raise ValueError('Too many tuples requested for the number of items!')

    random.seed()

    picked  = [] # Used to record picked seeds
    seen    = []
    tup     = [] # Temporary tuple
    tuples  = [] # Search tuples to return
    while l:
        seed = random.choice(seeds)
        while seed in picked:
            seed = random.choice(seeds)

        picked.append(seed)
        tup.append(seed)

        if len(tup) == n:
            ord_tup = list(tup)
            ord_tup.sort()
            ordered = ' '.join(ord_tup)

            if not ordered in seen:
                seen.append(ordered)
                tuples.append(' '.join(tup))
                l -= 1

            tup = []
            picked = []

    return tuples

def build_random_tuples(seeds, n=3, l=10, outdir=None, talkative=False):
    """Wrapper for calling BootCaT's build_random_tuples.pl. A file "tuples.txt"
        (in outdir) will contain the resulting search tuples returned by this
        function if outdir is a valid directory and outdir/tuples.txt can be
        written to.

        @type  seeds: iterable object
        @param seeds: A list/tuple/whatever of seeds (str) that will be used to
                create search tuples.
        @type  n: int
        @param n: The number of seeds present in each tuple. Passed directly to
                BootCaT's build_random_tuples.pl (-n).
        @type  l: int
        @param l: The number of search tuples to create. Passed directly to
                BootCaT's build_random_tuples.pl (-l).
        @type  outdir: str
        @param outdir: The path of the directory to create tuples.txt in.
        @type  talkative: bool
        @param talkative: Whether or not to print info as we progress.
        """
    #output, input = popen2('%sbuild_random_tuples.pl -n%d -l%d' % (PERLPREFIX, n, l))
    #input.write('\n'.join(seeds))
    #input.close()

    #searchtuples = [l[:-1] for l in output.readlines()] # Read output and chop off \n's
    searchtuples = _build_random_tuples(seeds, n=n, l=l) # This line replaces the block above

    if talkative:
        print _('Search tuples:')
        for t in searchtuples:
            print '\t%s' % (t)

    if outdir and os.path.isdir(outdir):
        f = open( os.path.join(outdir, 'tuples.txt'), 'w' )
        f.write('\n'.join(searchtuples) + '\n')
        f.close()

    return tuple(searchtuples)

def collect_urls_from_yahoo(searchtuples, count=10, lang='default', appid='00000000'):
    """A (Python) replacement for BootCaT's collect_urls_from_yahoo.pl."""
    from yahoo.search import web

    urls = set()

    for query in searchtuples:
        search = web.WebSearch(appid, query=query, results=count, language=lang)
        results = search.parse_results()

        for res in results:
            urls.add(res.Url)

    return urls

def get_urls(searchtuples, count=10, engine='yahoo', lang=None, outdir=None, talkative=False):
    """Wrapper for BootCaT's collect_urls_from_{google,yahoo}.pl scripts. A file
        "urls.txt" (in outdir) will contain the resulting URLs returned by this
        function if outdir is a valid directory and outdir/urls.txt is writable.

        @type  tuplesfile: str (filename)
        @param tuplesfile: The file containing the search tuples to use (as
                create by build_random_tuples().
        @type  count: int
        @param count: The number of results to collect per search tuple. Passed
                directly to BootCaT's collect_urls_from_{google,yahoo}.pl (-c).
        @type  engine: str
        @param engine: The search engine to use. Must be 'yahoo' (default),
                because Google currently requires an API key and Yahoo doesn't.
        @type  lang: str
        @param lang: Optional language argument to pass to
                collect_urls_from_{google,yahoo}.pl. Validity not checked.
        @type  outdir: str
        @param outdir: The path of the directory to create urls.txt in.
        @type  talkative: bool
        @param talkative: Whether or not to print info as we progress.

        @rtype:  tuple
        @return: Unique URLs returned by the search engine.
        """

    if engine != 'yahoo':
        raise Exception('Unknown or unsupported search engine: %s' % engine)

    # The block below uses BootCaT and is replaced by collect_urls_from_yahoo() above.
    #lang = lang and ('-l %s' % lang) or ''
    #output, input = popen2('%scollect_urls_from_%s.pl -c %d %s %s' % (PERLPREFIX, engine, count, lang, tuplesfile))
    #input.close()

    #urlset = set()

    #for line in output.readlines():
    #    if not line.startswith('CURRENT_QUERY '):
    #        urlset.add(line[:-1]) # Add chopped line to set

    if lang is None:
        lang = 'default'
    urlset = collect_urls_from_yahoo(searchtuples, count, lang)

    if talkative:
        print _("URLs:")
        for url in urlset:
            print '\t%s' % (url)

    if outdir and os.path.isdir(outdir):
        f = open( os.path.join(outdir, 'urls.txt'), 'w')
        f.write('\n'.join(urlset) + '\n')
        f.close()

    return tuple(urlset)

def download_urls(urls, outdir=None, crawldepth=0, siteonly=False, talkative=False):
    """Downloads all URLs in urls to outdir/data. Files are renamed to
        _hash_.html where _hash_ is the md5sum of the URL. The original URL is
        saved as an HTML comment in the first line of the downloaded file.

        @type  urls: iterable
        @param urls: An iterable collection of strings (URLs to download).
        @type  outdir: str
        @param outdir: The path of the directory to download to (outdir/data).
        @type  talkative: bool
        @param talkative: Whether or not to print info as we progress.
        """

    if not outdir or not os.path.isdir(outdir):
        outdir = '.'

    datadir = os.path.join(outdir, 'data')
    if not os.path.exists(datadir):
        os.mkdir(datadir)

    localpages = []

    if talkative:
        print _("Downloading URLs:")

    for url in urls:
        site = ''
        if siteonly:
            parts = url.split('/')
            site = '%s//%s' % (parts[0], parts[2])
        localpages = crawl_url(url, datadir=datadir, depth=crawldepth, site=site, talkative=talkative)

    return localpages and tuple(localpages) or ()

def url_is_text(url):
    """Make sure that the given URL has a text/* mimetype by checking its HTTP header."""
    host, path = urlparse.urlsplit(url)[1:3]

    try:
        conn = httplib.HTTPConnection(host)
        conn.request('HEAD', path)
        response = conn.getresponse()
    except:
        return False

    return response.getheader('content-type').startswith('text/')

def crawl_url(url, browser=None, datadir='data', depth=0, site='', talkative=False):
    """Downloads C{url} to C{datadir} using C{browser} and recurse with all
        links on that page as long as C{depth >= 0} and the link's URL starts
        with C{site}.

        @rtype : list
        @return: A list of local filenames downloaded.
        """
    if depth < 0:
        return None

    if browser is None:
        browser = Browser()
        browser.addheaders = (
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('User-agent', 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)') # We're Firefox! :P
        )
        browser.set_handle_gzip(True)
        browser.set_handle_redirect(True)
        browser.set_handle_refresh(False)
        browser.set_handle_robots(True)
        browser.set_handled_schemes(['http', 'https'])
        browser.set_proxies({})

    files = []

    fname = os.path.join(datadir, '%s.html' % md5.new(url).hexdigest())
    if os.path.exists(fname):
        # The URL was not previously downloaded
        if talkative:
            print _('\t%s => [Previously downloaded]') % (url)
    elif url_is_text(url):
        html = ''
        try:
            html = filterhtml(browser.open(url).get_data())
        except Exception, exc:
            if talkative:
                print _('\t%s => ERROR: %s') % (url, exc)
            return None

        f = open(fname, 'w')
        f.write('<!-- URL: %s -->\n' % url)
        f.write(html)
        f.close()

        if talkative:
            print '\t%s => %s' % (url, fname)

        files.append(fname)
        if browser.viewing_html():
            for link in browser.links():
                if not link.url or link.url.startswith('javascript:') or link.url.startswith('mailto:'):
                    # Links with href="" or href="javascript:..." must be skipped
                    continue

                if link.url.startswith('http') and not link.url.startswith(site):
                    # We don't want to leave current site. NOTE: when site == '', the
                    # second part of the test above is never true.
                    continue

                if not link.url.startswith('http'):
                    # If we get here, link.url is relative to the current path, so we
                    # try have to join it with urlparse.urljoin
                    if link.url != browser.geturl():
                        link.url = urlparse.urljoin(browser.geturl(), link.url)
                    else:
                        continue

                downloaded = crawl_url(link.url, browser=browser, datadir=datadir, depth=depth-1, site=site, talkative=talkative)
                if downloaded:
                    files.extend(downloaded)

    return files

def convert_pages(localpages, outdir=None, talkative=False):
    """Converts all HTML files in localpages to text in outdir/data/. The
        text file's name will be the same as for its HTML source, only with a
        .txt extension in stead of .html.

        @type  localpages: iterable
        @param localpages: An iterable collection of filenames to convert.
        @type  outdir: str
        @param outdir: The path of the directory to put converted files (outdir/data).
        @type  talkative: bool
        @param talkative: Whether or not to print info as we progress.

        @rtype:  tuple
        @return: A tuple of filenames of converted text files.
        """
    if not outdir or not os.path.isdir(outdir):
        outdir = '.'

    datadir = os.path.join(outdir, 'data')
    if not os.path.exists(datadir):
        os.mkdir(datadir)

    textfiles = []

    if talkative:
        print _('Converting HTML to text:')

    for htmlfname in localpages:
        htmlfile = open(htmlfname)
        url = htmlfile.readline()[5:-5] # Strip the comment tag from the first
                                        # line and we have our URL a la
                                        # download_urls() above.
        html = htmlfile.read()

        # Try and decode 'html'
        foundenc = False
        for encoding in ('latin-1', 'utf-8'):
            try:
                html = html.decode(encoding)
                foundenc = True
                break
            except: pass

        if not foundenc:
            if talkative:
                print _("\t%s => ERROR: Couldn't decode HTML") % (htmlfname)
            continue

        try:
            text = html2text(html)
        except Exception, exc:
            if talkative:
                print '\t%s => ERROR: %s' % (htmlfname, exc)
            continue

        if isinstance(text, unicode):
            text = text.encode('utf-8')

        text = filtertext(text)

        fname = '%s.txt' % (htmlfname[:-5])
        textfile = open(fname, 'w')
        if url:
            textfile.write('[ %s ]\n' % (url))
        textfile.write(text)
        textfile.close()

        if talkative:
            print '\t%s => %s' % (htmlfname, fname)
        textfiles.append(fname)

    return tuple(textfiles)

def filterhtml(html):
    """Filters out unnecessary HTML before it is parsed into text.
        TODO: Implement this!

        @param html: The HTML text to filter.
        @rtype:  str
        @return: The filtered HTML."""
    return html

def filtertext(text):
    """Filters out unnecessary strings after it was parsed into text.
        TODO: Implement this!

        @param text: The text to filter.
        @rtype:  str
        @return: The filtered text."""
    return text



def create_option_parser():
    """Creates command-line option parser for when this script is used on the
        command-line. Run "corpus_collect.py -h" for help regarding options."""
    from optparse import OptionParser
    usage='Usage: %prog [<options>] [<seedfile>]'
    parser = OptionParser(usage=usage)

    parser.add_option(
        '-q', '--quiet',
        dest='quiet',
        action="store_true",
        help=_('Suppress output (quiet mode).'),
        default=False
    )
    parser.add_option(
        '-o', '--output-dir',
        dest='outputdir',
        help=_('Output directory to use.'),
        default='.'
    )

    # Options controlling search tuples
    parser.add_option(
        '-n', '--num-elements',
        dest='numelements',
        help=_('The number of seeds elements per tuple.'),
        type="int",
        default=3
    )
    parser.add_option(
        '-l', '--tuple-list-length',
        dest='tuplelength',
        help=_('The number of tuples to create from seeds.'),
        type='int',
        default=10
    )
    parser.add_option(
        '-u', '--urls-per-tuple',
        dest='urls',
        help=_('The number of search results to retrieve per tuple.'),
        type='int',
        default=10
    )

    # Crawling options
    parser.add_option(
        '-d', '--crawl-depth',
        dest='crawldepth',
        type='int',
        default=0,
        help=_('Follow this many levels of links from each URL.')
    )
    parser.add_option(
        '-S', '--no-site-only',
        dest='siteonly',
        action='store_false',
        default=True,
        help=_('When following the links on a page, do not stay on the original site.')
    )

    # Continuation (from previous work) options
    parser.add_option(
        '-t', '--tuple-file',
        dest='tuplefile',
        metavar='TFILE',
        help=_('Do not calculate tuples, use tuples from TFILE.'),
        default=''
    )
    parser.add_option(
        '-U', '--url-file',
        dest='urlfile',
        metavar='UFILE',
        help=_("Do not search for URLs, use URLs from UFILE."),
        default=''
    )
    parser.add_option(
        '-p', '--page-dir',
        dest='pagedir',
        metavar='DIR',
        help=_("Do not download pages, use pages in directory DIR."),
        default=''
    )

    # Step-skipping options
    parser.add_option(
        '--skip-urls',
        dest='skipurls',
        action='store_true',
        help=_('Skip URL collection. Implied by -U.'),
        default=False
    )
    parser.add_option(
        '--skip-download',
        dest='skipdownloads',
        action='store_true',
        help=_("Skip downloading of URLs. Implied by -p."),
        default=False
    )
    parser.add_option(
        '--skip-convert',
        dest='skipconvert',
        action='store_true',
        help=_('Skip convertion of HTML to text.'),
        default=False
    )

    parser.add_option(
        '-V', '--version',
        dest='ver',
        default=False,
        action='store_true',
        help=_('Display version information and exit.')
    )

    return parser

def main():
    """Main entry-point for command-line usage."""
    options, args = create_option_parser().parse_args()

    if options.ver:
        from __version__ import print_version_info
        print_version_info('corpus_collect.py')
        exit(0)

    outputdir = options.outputdir
    l = options.tuplelength
    n = options.numelements
    q = options.quiet
    u = options.urls

    f = os.sys.stdin

    skipTuples   = False # You can't really skip this step without having other input to work with.
    skipUrls     = options.skipurls
    skipDownload = options.skipdownloads
    skipConvert  = options.skipconvert

    if options.tuplefile:
        skipTuples = True
    if options.urlfile:
        skipTuples = skipUrls = True
    if options.pagedir:
        skipTuples = skipUrls = skipDownload = True

    #print 'Skipping options: %s %s %s' % (skipTuples, skipUrls, skipDownload)

    # Step 1: Get search tuples
    if skipTuples:
        searchtuples = ()
        if not skipUrls and not skipDownload:
            tuplefile = open(options.tuplefile)
            searchtuples = tuple([ line[:-1] for line in tuplefile.readlines() ])
    else:
        if args:
            if os.path.exists(args[0]):
                f = open(args[0])
            else:
                print usage
                exit(1)

        if not q:
            print _('Reading seeds from %s') % (f.name)
        seeds = f.read().split()

        searchtuples = build_random_tuples(seeds, n=n, l=l, outdir=outputdir, talkative=not q)

    # Step 2: Collect URLs from search results of searching for search tuples
    if skipUrls:
        urls = ()
        if not skipDownload:
            urlfile = open(options.urlfile)
            urls = tuple([ line[:-1] for line in urlfile.readlines() ])
    else:
        urls = get_urls(searchtuples, count=u, outdir=outputdir, talkative=not q)

    # Step 3: Download the URLs to the local machine
    if skipDownload:
        if not os.path.isdir(options.pagedir):
            raise ValueError(_('Not a valid directory: %s') % (options.pagedir))

        localpages = []

        def htmlfilter(arg, dir, files):
            files[:] = [f for f in files if f.endswith('html')]
            for f in files:
                localpages.append( os.path.join(dir, f) )

        os.path.walk(options.pagedir, htmlfilter, None)
        localpages = tuple(localpages)
    else:
        localpages = download_urls(
            urls,
            outdir=outputdir,
            crawldepth=options.crawldepth,
            siteonly=options.siteonly,
            talkative=not q
        )

    # Step 4: Convert downloaded pages to text
    if not skipConvert:
        texts = convert_pages(localpages, outdir=outputdir, talkative=not q)



if __name__ == '__main__':
    main()
