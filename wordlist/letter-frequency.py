#!/usr/bin/python

import string
import locale
import codecs
import sys
from optik import OptionParser

parser = OptionParser()
parser.add_option("-i", "--input-file", dest="filename",
                  help="wordlist FILE to parse and evaluate, use - to read form stdin", metavar="FILE")
parser.add_option("-v", "--verbose",
                  action="store_true", dest="verbose", default=0,
                  help="print python dictionaries and frequency percentages")
parser.add_option("-l", "--locale", dest="inputlocale", default=locale.getdefaultlocale(),
                  help="locale to use for selection of valid characters, default is the current locale", metavar="LOCALE")
(options, args) = parser.parse_args()

if options.filename is None:
  parser.print_help()
  sys.exit()

if options.filename == "-": options.filename = '/dev/stdin'
input = open(options.filename, 'r')
freq = {}
locale.setlocale(locale.LC_ALL, options.inputlocale)

line = input.readline()
total = 0
#while line != "":
#  count, word = string.split(line, maxsplit=1)
#  for c in word:
#    if c in string.letters + "-'":
#      total += int(count)
#      if freq.has_key(c):
#        freq[c] += int(count)
#      else:
#        freq[c] = int(count)
#  line = input.readline()

while line != "":
	word = line
	for c in word:
		if c in string.letters + "-'":
			if freq.has_key(c):
				freq[c] += 1
			else:
				freq[c] = 1
	line = input.readline()

input.close()

sorted = []
for n in range(len(freq)):
  max = 0
  for key in freq.keys():
     if key not in sorted:
       if freq[key] > max:
         max = freq[key]
         maxkey = key
  sorted = sorted + [maxkey]
  
if options.verbose:
  print freq
  print sorted
  print total

# Print MySpell ready frequency string
if options.verbose: print "MySpell freqencies"
freqs = ""
for c in sorted:
  freqs += c
print freqs

# Print frequency percentages
if options.verbose:
  print
  print "Frequency percentages"
  for c in sorted:
   print "%s : %2.2f%%" % (c, 100.0 * freq[c] / total )
