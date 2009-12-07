#!/usr/bin/python

import sys
import string

f=open("/dev/stdin", "r")

word = ""

line = f.readline()
while( line != ""):
  ncount, nword = string.split(line)
  tcount = string.atoi(ncount)
  if( word != nword and word != "" ):
     print '%10d %s' % (count, word)
     word = nword
     count = tcount
  elif( word != nword and word == ""):
     word = nword
     count = tcount
  else:
     count += tcount
  line = f.readline()
print '%10d %s' % (count, word)
