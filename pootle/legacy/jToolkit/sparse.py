#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""simple parser / string tokenizer
rather than returning a list of token types etc, we simple return a list of tokens...
each tokenizing function takes a string as input and returns a list of tokens
"""

# Copyright 2002, 2003 St James Software
# 
# This file is part of jToolkit.
#
# jToolkit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# jToolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with jToolkit; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import bisect

def stringeval(input):
  """takes away repeated quotes (escapes) and returns the string represented by the input"""
  stringchar = input[0]
  if input[-1] != stringchar or stringchar not in ("'",'"'):
    # scratch your head
    raise ValueError, "error parsing escaped string: %r" % input
  return input[1:-1].replace(stringchar+stringchar,stringchar)

def stringquote(input):
  """escapes quotes as neccessary and returns a string representing the input"""
  if "'" in input:
    if '"' in input:
      return '"' + input.replace('"', '""') + '"'
    else:
      return '"' + input + '"'
  else:
    return "'" + input + "'"

def findall(src, substr):
  pos = 0
  while True:
    pos = src.find(substr, pos)
    if pos == -1:
      break
    yield pos
    pos += 1

class ParserError(ValueError):
  """Intelligent parser error"""
  def __init__(self, parser, message, tokennum):
    """takes a message and the number of the token that caused the error"""
    tokenpos = parser.findtokenpos(tokennum)
    line, charpos = parser.getlinepos(tokenpos)
    ValueError.__init__(self, "%s at line %d, char %d (token %r)" % \
        (message, line, charpos, parser.tokens[tokennum]))
    self.parser = parser
    self.tokennum = tokennum

class SimpleParser:
  """this is a simple parser"""
  def __init__(self, defaulttokenlist=None, whitespacechars=" \t\r\n", includewhitespacetokens=0):
    if defaulttokenlist is None:
      self.defaulttokenlist = ['<=', '>=', '==', '!=', '+=', '-=', '*=', '/=', '<>']
      self.defaulttokenlist.extend('(),[]:=+-')
    else:
      self.defaulttokenlist = defaulttokenlist
    self.whitespacechars = whitespacechars
    self.includewhitespacetokens = includewhitespacetokens
    self.standardtokenizers = [self.stringtokenize, self.removewhitespace, self.separatetokens]
    self.quotechars = ('"', "'")
    self.endquotechars = {'"':'"',"'":"'"}
    self.unicodeprefix = None
    self.stringescaping = 1
    self.tokenposcache = {}
    self.lineposcache = {}

  def stringtokenize(self, input):
    """makes strings in input into tokens..."""
    tokens = []
    laststart = 0
    instring = 0
    endstringchar, escapechar = '', '\\'
    gotclose, gotescape = 0, 0
    for pos in range(len(input)):
      char = input[pos]
      if instring:
        if self.stringescaping and (gotescape or char == escapechar) and not gotclose:
          gotescape = not gotescape
        elif char == endstringchar:
          gotclose = not gotclose
        elif gotclose:
          tokens.append(input[laststart:pos])
          instring, laststart, endstringchar = 0, pos, ''
      if not instring:
        if char in self.quotechars:
          if self.unicodeprefix and input[pos-len(self.unicodeprefix):pos] == self.unicodeprefix:
            pos -= 1
          if pos > laststart: tokens.append(input[laststart:pos])
          instring, laststart, endstringchar, gotclose = 1, pos, self.endquotechars[char], 0
    if laststart < len(input): tokens.append(input[laststart:])
    return tokens

  def keeptogether(self, input):
    """checks whether a token should be kept together"""
    return self.isstringtoken(input)

  def isstringtoken(self, input):
    """checks whether a token is a string token"""
    return input[:1] in self.quotechars or input[:1] == self.unicodeprefix and input[1:][:1] in self.quotechars

  def separatetokens(self, input, tokenlist = None):
    """this separates out tokens in tokenlist from whitespace etc"""
    if self.keeptogether(input): return [input]
    if tokenlist is None:
      tokenlist = self.defaulttokenlist
    # loop through and put tokens into a list
    tokens = []
    pos = 0
    laststart = 0
    while pos < len(input):
      foundtoken = 0
      for token in tokenlist:
        if input[pos:pos+len(token)] == token:
          if laststart < pos: tokens.append(input[laststart:pos])
          tokens.append(token)
          pos += len(token)
          foundtoken, laststart = 1, pos
          break
      if not foundtoken: pos += 1
    if laststart < len(input): tokens.append(input[laststart:])
    return tokens

  def removewhitespace(self, input):
    """this removes whitespace but lets it separate things out into separate tokens"""
    if self.keeptogether(input): return [input]
    # loop through and put tokens into a list
    tokens = []
    pos = 0
    inwhitespace = 0
    laststart = 0
    for pos in range(len(input)):
      char = input[pos]
      if inwhitespace:
        if char not in self.whitespacechars:
          if laststart < pos and self.includewhitespacetokens: tokens.append(input[laststart:pos])
          inwhitespace, laststart = 0, pos
      else:
        if char in self.whitespacechars:
          if laststart < pos: tokens.append(input[laststart:pos])
          inwhitespace, laststart = 1, pos
    if laststart < len(input) and (not inwhitespace or self.includewhitespacetokens):
      tokens.append(input[laststart:])
    return tokens

  def applytokenizer(self, inputlist, tokenizer):
    """apply a tokenizer to a set of input, flattening the result"""
    tokenizedlists = [tokenizer(input) for input in inputlist]
    joined = []
    map(joined.extend, tokenizedlists)
    return joined

  def applytokenizers(self, inputlist, tokenizers):
    """apply a set of tokenizers to a set of input, flattening each time"""
    for tokenizer in tokenizers:
      inputlist = self.applytokenizer(inputlist, tokenizer)
    return inputlist

  def tokenize(self, source, tokenizers=None):
    """tokenize the input string with the standard tokenizers"""
    self.source = source
    if tokenizers is None:
      tokenizers = self.standardtokenizers
    self.tokens = self.applytokenizers([self.source], tokenizers)
    return self.tokens

  def refreshposcache(self):
    """refreshes the cache of token positions"""
    self.tokenposcache = {}
    self.lineposcache = list(findall(self.source, "\n"))
    self.findtokenpos(len(self.tokens)-1)

  def findtokenpos(self, tokennum):
    """finds the position of the given token in the input"""
    if tokennum in self.tokenposcache:
      return self.tokenposcache[tokennum]
    cachedtokennums = [cachedtokennum for cachedtokennum in self.tokenposcache if cachedtokennum <= tokennum]
    if cachedtokennums:
      starttokennum = max(cachedtokennums)
      currenttokenpos = self.tokenposcache[starttokennum]
    else:
      starttokennum = 0
      currenttokenpos = 0
    for currenttokennum in range(starttokennum, tokennum+1):
      currenttokenpos = self.source.find(self.tokens[currenttokennum], currenttokenpos)
      self.tokenposcache[currenttokennum] = currenttokenpos
    return currenttokenpos

  def getlinepos(self, tokenpos):
    """finds the line and character position of the given character"""
    if self.lineposcache:
      line = bisect.bisect_left(self.lineposcache, tokenpos)
      if line:
        linestart = self.lineposcache[line-1]
        charpos = tokenpos - linestart
      else:
        linestart = 0
        charpos = tokenpos + 1
      line += 1
    else:
      sourcecut = self.source[:tokenpos]
      line = sourcecut.count("\n")+1
      charpos = tokenpos - sourcecut.rfind("\n")
    return line, charpos

  def raiseerror(self, message, tokennum):
    """raises a ParserError"""
    raise ParserError(self, message, tokennum)


