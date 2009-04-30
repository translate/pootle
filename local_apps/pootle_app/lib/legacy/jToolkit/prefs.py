#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""manages preferences files that are hierarchical and nice for both humans and python"""

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

from pootle_app.lib.legacy.jToolkit import sparse
import os
import sys

class indent(str):
  def __init__(self, value):
    self.level = 0
  def setlevel(self, level):
    self.level = level
  def __repr__(self):
    return "indent(%d)" % self.level

def evaluateboolean(value, default=False):
  """evaluates the pref value as a boolean"""
  if value is None:
    return default
  if isinstance(value, (str, unicode)):
    if value.isdigit():
      value = int(value)
    else:
      value = value.lower() == 'true'
  return bool(value)

class PrefNode(object):
  def __init__(self, parent, keypart):
    if keypart is None:
      self.__dict__["_parser"] = parent
      self.__dict__["__root__"] = self
      self.__dict__["__key__"] = ""
      self.__dict__["_setvalue"] = getattr(parent, "setvalue")
      self.__dict__["_removekey"] = getattr(parent, "removekey")
      self.__dict__["_resolve"] = getattr(parent, "resolveconfigobject")
      self.__dict__["_assignments"] = {}
    else:
      self.__dict__["__root__"] = parent.__root__
      if parent.__key__ == "":
        self.__dict__["__key__"] = keypart
      else:
        self.__dict__["__key__"] = parent.__key__ + "." + keypart

  def __setattr__(self, keypart, value):
    parentpart = self.__key__
    if len(parentpart) > 0:
      parentpart += "."
    self.__root__._setvalue(parentpart + keypart, value)

  def __delattr__(self, keypart):
    if not keypart in self.__dict__:
      object.__delattr__(self, keypart)
    elif self.__key__ == "":
      self.__root__._removekey(keypart)
    else:
      self.__root__._removekey(self.__key__ + "." + keypart)

  def __getattr__(self, attr):
    """tries to find the attribute, handling unicode if given"""
    # TODO: add default support
    if "." in attr:
      if self.__root__ == self:
        return self._parser.getvalue(attr)
      return self.__root__.__getattr__(self.__key__ + "." + attr)
    if isinstance(attr, basestring) and attr in self.__dict__:
      return self.__dict__[attr]
    if not (isinstance(attr, unicode) or "." in attr):
      return getattr(super(PrefNode, self), attr)
    else:
      raise AttributeError("%r PrefNode object has no attribute %r" % (self.__class__.__name__, attr))

  def __hasattr__(self, attr):
    """tries to find if attribute is present, handling unicode if given"""
    if "." in attr:
      if self.__root__ == self:
        return self._parser.hasvalue(attr)
      return self.__root__.__hasattr__(self.__key__ + "." + attr)
    if isinstance(attr, basestring):
      if attr in self.__dict__:
        return True
    if not (isinstance(attr, unicode) or "." in attr):
      return hasattr(super(PrefNode, self), attr)
    return False

  def __repr__(self):
    return self.__key__

  def __str__(self):
    return self.__key__

  def __getstate__(self):
    return (self.__root__._resolve.im_self.__getstate__(), self.__key__)

  def __setstate__(self, state):
    parserText, key = state
    parser = PrefsParser()
    parser.parse(parserText)
    # Now we need some way of making self the object denoted by state[1]
    keys = key.split(".")
    oldobject = parser.__root__
    parent = None
    if not len(keys) == 1 and keys[0] == "":
      for keypart in keys:
        parent = oldobject
        oldobject = oldobject.__getattr__(keypart)

    self.__dict__["__key__"] = key
    if oldobject.__dict__.has_key("__root__"):
      if key == "":
        self.__dict__["__root__"] = self
      else:
        self.__dict__["__root__"] = oldobject.__root__
    if oldobject.__dict__.has_key("__base__"):
      self.__dict__["__base__"] = oldobject.__base__
    PrefNode.copyattrs(oldobject, self)

    if parent == None:
      parser.__root__ = self
    else:
      parent.__setattr__(keys[-1], self)

  def getlabel(self):
    return getattr(self, "__base__", self.__key__)

  def copy(oldobject, parent, keypart):
    """
    Returns a PrefNode identical to this one, but with a different name and parent
    Assignments are duplicated in __root__._assignments so they will be noticed by getsource
    """
    newobject = PrefNode(parent, keypart)
    PrefNode.copyattrs(oldobject, newobject)
    return newobject

  def copyattrs(oldobject, newobject):
    for childkeypart in oldobject.__dict__:
      if childkeypart in ("__root__", "__key__", "__base__"): continue
      oldchild = oldobject.__dict__[childkeypart]
      if isinstance(oldchild, PrefNode):
        newobject.__dict__[childkeypart] = oldchild.copy(newobject, childkeypart)
      else:
        newobject.__dict__[childkeypart] = oldchild
        label = newobject.getlabel() + '.' + childkeypart
        newobject.__root__._assignments[label] = oldchild

  def relocate(self, newkey):
    self.__dict__["__base__"] = self.__key__
    self.__dict__["__key__"] = newkey
    for childkeypart in self.__dict__:
      if childkeypart in ("__root__", "__key__", "__base__"): continue
      child = self.__dict__[childkeypart]
      if isinstance(child, PrefNode):
        child.relocate(newkey + "." + childkeypart)

  def renamepref(self,name,newname):
    """
    Rename a pref by removing it and adding a new one
    name is the pref to rename
    newname is what that pref will be renamed to
    """
    value = getattr(self,name)
    setattr(self,newname,value)
    delattr(self,name)

  def iteritems(self, sorted=False):
    """iterate through the items, sort them by key if sorted"""
    if sorted:
      childitems = self.__dict__.items()
      childitems.sort()
    else:
      childitems = self.__dict__.iteritems()
    for childkeypart, child in childitems:
      if childkeypart in ("__root__", "__key__", "__base__"): continue
      if childkeypart in ("_parser", "_setvalue", "_removekey", "_resolve", "_assignments"): continue
      yield childkeypart, child

  def getparser(self):
    """finds the parser object this belongs to"""
    return self.__root__._parser

# TODO: allow UnresolvedPref to resolve prefs using Python imports

class UnresolvedPref:
  def __init__(self, root, label):
    self.__dict__["__root__"] = root
    self.__dict__["__key__"] = label

  def __repr__(self):
    return self.__key__

  def __str__(self):
    return self.__key__

  def resolve(self):
    return self.__root__._resolve(self.__key__)


# TODO: improve handling of object values - strings, integers, classes, modules etc
class PrefsParser(sparse.SimpleParser, object):
  def __init__(self, filename=None):
    """sets up the PrefsParser"""
    sparse.SimpleParser.__init__(self, includewhitespacetokens = 1)
    self.unicodeprefix = "u"
    self.standardtokenizers = [self.commenttokenize, self.stringtokenize, \
        self.removewhitespace, self.splitatnewline, self.separatetokens]
    self.__root__ = PrefNode(self, None)

    # Initialise all the token holders
    if filename is None:
      self.parse("")
    else:
      self.parsefile(filename)
    self.__initialized__ = True

  def __setattr__(self, keypart, value):
    """we need to be able to act as the root node in case setattr is called on us directly"""
    if getattr(self, "__initialized__", False) and not self.__hasattr__(keypart) and keypart not in ("changes", "filename"):
      self.setvalue(keypart, value)
    else:
      super(PrefsParser, self).__setattr__(keypart, value)

  def __getstate__(self):
    """Prepares the object for pickling

    This preserves the only thing we actually need to preserve - the text returned from self.getsource()"""
    return self.getsource()

  def __setstate__(self, state):
    """Unpickles the object

    This takes a prefsfile source, created by another parser, and creates a new parser"""
    self.__init__()   # In case it hasn't been called
    self.parse(state)

  def keeptogether(self, input):
    """checks whether a token should be kept together"""
    # don't retokenize strings
    return sparse.SimpleParser.keeptogether(self, input) or self.iscommenttoken(input)

  def stringtokenize(self, input):
    """makes strings in input into tokens... but keeps comment tokens together"""
    if self.iscommenttoken(input):
      return [input]
    return sparse.SimpleParser.stringtokenize(self, input)

  def iscommenttoken(self, input):
    """checks whether a token is a comment token"""
    return input[:1] == "#"

  def commenttokenize(self, input):
    """makes comments in input into tokens..."""
    if sparse.SimpleParser.keeptogether(self, input): return [input]
    tokens = []
    incomment = False
    laststart = 0
    startcommentchar, endcommentchar = '#', '\n'
    for pos in range(len(input)):
      char = input[pos]
      if incomment:
        if char == endcommentchar:
          if pos > laststart: tokens.append(input[laststart:pos])
          incomment, laststart = False, pos
      else:
        if char == startcommentchar:
          if pos > laststart: tokens.append(input[laststart:pos])
          incomment, laststart = True, pos
    if laststart < len(input): tokens.append(input[laststart:])
    return tokens

  def splitatnewline(self, input):
    """splits whitespace tokens at newline, putting the newline at the beginning of the split strings
    whitespace tokens not containing newlines are discarded"""
    if self.keeptogether(input): return [input]
    if input.isspace():
      lastnewline = input.rfind("\n")
      if lastnewline != -1:
        return [input[lastnewline:]]
      return []
    return [input]

  def handleindents(self):
    """finds indents in tokens and replaces them with indent objects"""
    indentedtokens = []
    indentstack = [0]
    for tokennum, token in enumerate(self.tokens):
      if token[:1] == "\n":
        if tokennum+1 < len(self.tokens) and self.iscommenttoken(self.tokens[tokennum+1]):
          # treat indents before comments as whitespace, by removing them
          continue
        tokenlength = len(token[1:])
        if tokenlength <= indentstack[-1]:
          if tokenlength not in indentstack:
            self.raiseerror("invalid indentation", tokennum)
          indentstack = indentstack[:indentstack.index(tokenlength)+1]
        else:
          indentstack.append(tokenlength)
        token = indent(token)
        token.setlevel(indentstack.index(tokenlength))
      indentedtokens.append(token)
    if len(indentedtokens) > 0 and not isinstance(indentedtokens[0], indent):
      indentedtokens = [indent("")] + indentedtokens
    self.tokens = indentedtokens

  def parseassignments(self):
    """parses all the assignments from the tokenized preferences"""
    self.__dict__.setdefault('removals',{})
    self.__dict__.setdefault('valuepos',{})
    self.__dict__.setdefault('commentpos',{})
    self.__dict__.setdefault('sectionstart',{})
    self.__dict__.setdefault('sectionend',{})
    assignvar = None
    operation = None
    lastcomment = None
    lastvalue = None
    lastsection = None
    lastindent = indent("")
    context = {}
    indentlevels = {}
    self.refreshposcache()
    for tokennum, token in enumerate(self.tokens):
      if isinstance(token, indent):
        if token.level < lastindent.level:
          parentcontext = ".".join([context[level] for level in range(token.level)])
          for level in range(token.level, lastindent.level):
            if level in context:
              if not parentcontext:
                childcontext = context[level]
              else:
                childcontext = parentcontext + "." + context[level]
              self.sectionend[childcontext] = (tokennum, indentlevels[level+1])
              parentcontext = childcontext
              del context[level]
        elif token.level > lastindent.level:
          if operation == ':':
            operation = None
          else:
            self.raiseerror("indent without preceding :", tokennum)
        lastindent = token
        indentlevels[lastindent.level] = token
      elif self.iscommenttoken(token):
        # if the last value or section found is on the same line
        # as this comment then this comment refers to that pref
        lastcomment = (tokennum,token)
        if (lastvalue is not None) and (lastsection is not None):
          commentline,commentcharpos = self.getlinepos(self.findtokenpos(tokennum))
          valuenum,value = lastvalue
          vline,vpos = self.getlinepos(self.findtokenpos(valuenum))
          sectionnum,section = lastsection
          sectionline,sectionpos = self.getlinepos(self.findtokenpos(sectionnum))
          if commentline == vline:
            self.commentpos[value] = tokennum
            lastcomment = None
          elif commentline == sectionline:
            self.commentpos[section] = tokennum
            lastcomment = None
      elif token == '=':
        operation = token
      elif token == ':':
        context[lastindent.level] = assignvar
        operation = token
        prefixes = [context[level] for level in range(0, lastindent.level)]
        key = ".".join(prefixes+[assignvar])
        self.sectionstart[key] = tokennum
        lastsection = (tokennum,key)
      elif operation == '=':
        prefixes = [context[level] for level in range(0, lastindent.level)]
        key = ".".join(prefixes+[assignvar])
        realvalue = self.parsevalue(token)
        self.setvalue(key, realvalue)
        self.valuepos[key] = tokennum
        operation = None
        lastvalue = (tokennum,key)
      elif operation is None:
        if self.isstringtoken(token):
          if token.startswith(self.unicodeprefix):
            assignvar = sparse.stringeval(token.replace(self.unicodeprefix, "", 1)).decode("utf-8")
          else:
            assignvar = sparse.stringeval(token)
        else:
          assignvar = token
      else:
        self.raiseerror("I don't know how to parse that here", tokennum)
      # handle comments
      if operation == '=' or token == ':':
        # if the last comment found is on the line before this one then it refers to this pref/section
        if lastcomment is not None:
          commentnum,comment = lastcomment
          commentline,commentcharpos = self.getlinepos(self.findtokenpos(commentnum))
          myline,mycharpos = self.getlinepos(self.findtokenpos(tokennum))
          if myline == (commentline+1):
            if token == ':' and lastsection is not None:
              self.commentpos[lastsection[1]] = commentnum
            elif operation == '=' and lastvalue is not None:
              self.commentpos[lastvalue[1]] = commentnum

  def parse(self, prefsstring):
    """this parses a string and returns a base preferences object"""
    self.tokenize(prefsstring)
    self.handleindents()
    self.parseassignments()
    self.resolveinternalassignments()

  def parsefile(self, filename):
    """this opens a file and parses the contents"""
    self.filename = filename
    prefsfile = open(filename, 'r')
    contents = prefsfile.read()
    prefsfile.close()
    self.parse(contents)

  def savefile(self, filename=None, safesave=False):
    """this saves the source to the given filename"""
    if filename is None:
      filename = getattr(self, "filename")
    else:
      self.filename = filename
    contents = self.getsource()
    if safesave:
      dirpart = os.path.abspath(os.path.dirname(filename))
      filepart = os.path.basename(filename)
      tempfilename = os.tempnam(dirpart, filepart)
      prefsfile = open(tempfilename, 'w')
      prefsfile.write(contents)
      prefsfile.close()
      try:
        if os.name == 'nt' and os.path.exists(filename):
          os.remove(filename)
        os.rename(tempfilename, filename)
      except OSError, e:
        os.remove(tempfilename)
        raise e
    else:
      prefsfile = open(filename, 'w')
      prefsfile.write(contents)
      prefsfile.close()

  def hasvalue(self, key):
    """returns whether the given key is present"""
    keyparts = key.split(".")
    parent = self.__root__
    for keypart in keyparts:
      if not parent.__dict__.has_key(keypart):
        return False
      parent = parent.__dict__[keypart]
    return True

  def getvalue(self, key):
    """gets the value of the given key"""
    keyparts = key.split(".")
    parent = self.__root__
    for keypart in keyparts:
      if not parent.__dict__.has_key(keypart):
        raise IndexError("parent does not have child %r when trying to find %r" % (keypart, key))
      parent = parent.__dict__[keypart]
    return parent

  def setvalue(self, key, value):
    """set the given key to the given value"""
    if isinstance(value, PrefNode):
      value.relocate(key)
    # we don't store PrefNodes in assignments
    if not isinstance(value, PrefNode):
      self.__root__._assignments[key] = value
    keyparts = key.split(".")
    parent = self.__root__
    for keypart in keyparts[:-1]:
      if not parent.__dict__.has_key(keypart):
        parent.__dict__[keypart] = PrefNode(parent, keypart)
      child = parent.__dict__[keypart]
      # it is possible that this is overriding a value with a prefnode
      if not isinstance(child, PrefNode):
        child = PrefNode(parent, keypart)
        parent.__dict__[keypart] = child
      parent = child
    parent.__dict__[keyparts[-1]] = value

  def removekey(self, key):
    """remove the given key from the prefs tree. no node removal yet"""
    if key in self.__root__._assignments:
      del self.__root__._assignments[key]
    parent = self.__root__
    keyparts = key.split(".")
    for keypart in keyparts[:-1]:
      if not parent.__dict__.has_key(keypart):
        raise ValueError("key %s not found: %s has no child %s" % (key, parent.__key__, keypart))
      parent = parent.__dict__[keypart]
    attribname = keyparts[-1]
    if attribname in parent.__dict__:
      deadnode = parent.__dict__[attribname]
      if isinstance(deadnode, PrefNode):
        for childkey in deadnode.__dict__.keys():
          if childkey not in ("__root__", "__key__", "__base__"):
            self.removekey(key + "." + childkey)
      del parent.__dict__[attribname]
    else:
      raise ValueError("key %s not found: %s has no child %s" % (key, parent.__key__, attribname))
    self.removals[key] = True

  def parsevalue(self, value):
    """Parses a value set in a config file, and returns the correct object type"""
    if not isinstance(value, (str, unicode)):
      return value
    # If it's a string, try to parse it
    if (value.isdigit()):
      return int(value)
    elif (value[0] in ['"',"'"] and value[-1] == value[0]):
      return sparse.stringeval(value)
    elif (value[0] == 'u' and value[1] in ['"',"'"] and value[-1] == value[1]):
      return sparse.stringeval(value[1:]).decode("utf-8")
    else:
      return self.resolveconfigobject(value)

  def quotevalue(self, value):
    """converts a realvalue from parsevalue back to a string that can be stored in the prefs file"""
    if isinstance(value, int) or isinstance(value, long):
      return str(value)
    elif isinstance(value, PrefNode):
      return value.getlabel()
    elif isinstance(value, UnresolvedPref):
      return repr(value)
    elif isinstance(value, str):
      return sparse.stringquote(value)
    elif isinstance(value, unicode):
      return "u" + sparse.stringquote(value.encode("utf-8"))
    elif value is None:
      return ""
    else:
      raise ValueError("don't know how to quote %r value: %r" % (type(value), value))

  def resolveconfigobject(self, value):
    """Tries to find the object specified by "value" as a member of self
    Should be overridden if more types of objects are available"""
    valueparts = value.split(".")
    parent = self.__root__
    if hasattr(self.__root__, 'importmodules') and hasattr(self.__root__.importmodules,valueparts[0])\
       and not hasattr(self.__root__,valueparts[0]):
      parent = self.__root__.importmodules
    found = True
    for valuepart in valueparts:
      if isinstance(parent, PrefNode):
        # handle resolving for standard nodes...
        if hasattr(parent,valuepart):
          parent = parent.__dict__[valuepart]
        else:
          found = False
          break
      else:
        # handle resolving for other objects...
        if hasattr(parent, valuepart):
          parent = getattr(parent, valuepart)
        else:
          found = False
          break
    if found:
      if isinstance(parent, PrefNode):
        return parent.copy(self.__root__, value)
      else:
        # other objects can't be copied, so just return them...
        return parent
    elif value in self.__root__._assignments:
      return self.__root__._assignments[value]
    else:
      return UnresolvedPref(self.__root__, value)

  def resolveinternalassignments(self):
    """resolves any unresolved assignments that are internal (i.e. don't rely on imports)"""
    unresolved = len(self.__root__._assignments)
    lastunresolved = unresolved+1
    while unresolved < lastunresolved:
      lastunresolved = unresolved
      unresolved = 0
      for key in self.__root__._assignments:
        currentvalue = self.__root__._assignments[key]
        if isinstance(currentvalue, UnresolvedPref):
          unresolved += 1
          newvalue = currentvalue.resolve()
          if newvalue != currentvalue:
            self.setvalue(key, newvalue)

  def resolveimportmodules(self, mapmodulename=None):
    """actually imports modules specified in importmodules. not used unless explicitly called"""
    # import any required modules
    for refname, modulename in self.importmodules.iteritems():
      if mapmodulename:
        modulename = mapmodulename(modulename)
      try:
        module = __import__(modulename, globals(), locals())
      except ImportError, importmessage:
        errormessage = "Error importing module %r: %s\nPython path is %r" \
                       % (modulename, importmessage, sys.path)
        raise ImportError(errormessage)
      components = modulename.split('.')
      for component in components[1:]:
        module = getattr(module, component)
      importmodulekey = self.importmodules.__key__ + "." + refname
      self.setvalue(importmodulekey, module)
      # TODO: this is a hack. add this resolving into prefs so we don't have to delete the assignment
      # we currently delete the assignment so that the prefsfile can be safely saved
      del self.__root__._assignments[importmodulekey]
      modulevalue = getattr(self.importmodules, refname)

  def addKeyToDict(self, keyparts, value, dictionary):
    if len(keyparts) == 1:
      dictionary[keyparts[0]] = value
    else:
      dictionary.setdefault(keyparts[0],{})
      self.addKeyToDict(keyparts[1:],value,dictionary[keyparts[0]])

  def writeDict(self, dictionary, indent):
    result = ""
    sortedKeys = dictionary.keys()
    sortedKeys.sort()
    for key in sortedKeys:
      quotedkey = key
      if isinstance(quotedkey, unicode):
        try:
          quotedkey = str(quotedkey)
        except UnicodeError:
          pass
      if isinstance(quotedkey, unicode):
        quotedkey = "u" + sparse.stringquote(quotedkey.encode("utf-8"))
      else:
        testalphakey = quotedkey.replace("_", "a").replace(".", "0")
        if not (testalphakey[:1].isalpha() and testalphakey.isalnum()):
          quotedkey = sparse.stringquote(quotedkey)
      if isinstance(dictionary[key], dict):
        result += indent + quotedkey + ":\n"
        result += self.writeDict(dictionary[key], indent+"  ")
      else:
        result += indent + "%s = %s\n" % (quotedkey, dictionary[key])
    return result

  def findimmediateparent(self, key):
    """finds the most immediate indented parent of the given key"""
    keyparts = key.split(".")
    for keynum in range(len(keyparts),-1,-1):
      parentkey = ".".join(keyparts[:keynum])
      if parentkey in self.sectionend:
        return parentkey
    return None

  def addchange(self, tokennum, tokenschanged, newtokens, parentstart=None):
    """adds a change to self.changes"""
    if tokennum in self.changes:
      tokenchanges = self.changes[tokennum]
    else:
      tokenchanges = {}
      self.changes[tokennum] = tokenchanges
    if parentstart in tokenchanges:
      tokenchanges[parentstart].append((tokenschanged, newtokens))
    else:
      tokenchanges[parentstart] = [(tokenschanged, newtokens)]

  def getsource(self):
    """reconstructs the original prefs string with any changes that have been made..."""
    # changes is a dictionary, key is the position of the change
    # each value is a list of changes at that position
    # each change in the list is a tuple of the number of tokens to remove, and the new string
    self.changes = {}
    extradict = {}
    for key in self.__root__._assignments:
      currentvalue = self.__root__._assignments[key]
      keyfound = key in self.valuepos
      # try and handle key being encoded or not sensibly...
      if not keyfound:
        try:
          if isinstance(key, str):
            otherkey = key.decode("utf-8")
          elif isinstance(key, unicode):
            otherkey = key.encode("utf-8")
          keyfound = otherkey in self.valuepos
        except:
          pass
      if keyfound:
        # the key exists. change the value
        tokennum = self.valuepos[key]
        if currentvalue != self.parsevalue(self.tokens[tokennum]):
          self.addchange(tokennum, 1, self.quotevalue(currentvalue))
      else:
        # the key doesn't yet exist...
        keyparts = key.split(".")
        parentkey = self.findimmediateparent(key)
        if parentkey is not None:
          nodetokennum, nodeindent = self.sectionend[parentkey]
          parentstart = self.sectionstart[parentkey]
          keynum = parentkey.count(".") + 1
          childkey = ".".join(keyparts[keynum:])
          testalphakey = childkey.replace("_", "a").replace(".", "0")
          needsquoting = False
          if isinstance(testalphakey, unicode):
            try:
              testalphakey = testalphakey.encode("ascii")
            except UnicodeEncodeError:
              needsquoting = True
          if not (testalphakey[:1].isalpha() and testalphakey.isalnum()):
            needsquoting = True
          if needsquoting:
            childkey = self.quotevalue(childkey)
          quotedvalue = nodeindent + "%s = %s" % (childkey, self.quotevalue(currentvalue))
          self.addchange(nodetokennum, 0, quotedvalue, parentstart=parentstart)
        else:
          self.addKeyToDict(keyparts, self.quotevalue(currentvalue), extradict)
    for key in self.removals:
      if key in self.valuepos:
        tokennum = self.valuepos[key]
      elif key in self.sectionstart:
        tokennum = self.sectionstart[key]
      else:
        # then we don't know how to remove it
        # extras.append("# tried to remove key but could not find it: %s" % key)
        continue
      # to remove something, we search backwards from the value for an indent
      # and slice out the section from the indent to the value
      starttokennum = tokennum
      while starttokennum >= 0:
        if isinstance(self.tokens[starttokennum], indent):
          if starttokennum == 0:
            starttokennum += 1
          break
        starttokennum -= 1
      if starttokennum > 0:
        self.addchange(starttokennum, tokennum+1-starttokennum, "")
      else:
        # if we didn't find it, leave a note...
        self.addchange(tokennum, 1, "none")
    # now regenerate the source including the changes...
    tokennums = self.changes.keys()
    tokennums.sort()
    lastpos = 0
    newsource = ""
    for tokennum in tokennums:
      tokenpos = self.findtokenpos(tokennum)
      newsource += self.source[lastpos:tokenpos]
      totalremovetokens = 0
      parentstarts = self.changes[tokennum].keys()
      parentstarts.sort()
      parentstarts.reverse()
      for parentstart in parentstarts:
        for removetokens, newtext in self.changes[tokennum][parentstart]:
          if isinstance(newtext, unicode):
            newtext = newtext.encode("utf-8")
          newsource += newtext
          totalremovetokens += removetokens
      # work out the position of the last token, and put lastpos at the end of this token
      lasttokenpos = tokennum + totalremovetokens - 1
      if len(self.tokens) > lasttokenpos:
        lastpos = self.findtokenpos(lasttokenpos) + len(self.tokens[lasttokenpos])
    newsource += self.source[lastpos:]
    if extradict:
      if newsource and newsource[-1] != "\n": newsource += "\n"
      newsource += self.writeDict(extradict, "")
    return newsource

  def getcomment(self,key):
    """
    returns the comment associated with this the key given,
    or none if there is no such key
    """

    tokennum = self.commentpos.get(key,None)
    if tokennum:
      return self.tokens[tokennum]
    else:
      return None

  def __getattr__(self, attr):
    if attr in self.__dict__:
      return self.__dict__[attr]
    elif '__root__' in self.__dict__:
      if isinstance(attr, unicode):
        return self.__root__.__getattr__(attr)
      return getattr(self.__root__, attr)
    raise AttributeError("'PrefsParser' object has no attribute %s" % attr)

  def __hasattr__(self, attr):
    if attr in self.__dict__:
      return True
    elif '__root__' in self.__dict__:
      if isinstance(attr, unicode):
        return self.__root__.__hasattr__(attr)
      return hasattr(self.__root__, attr)

if __name__ == "__main__":
  import sys
  parser = PrefsParser()
  originalsource = sys.stdin.read()
  parser.parse(originalsource)
  import pickle
  pickled = pickle.dumps(parser)
  recreatedsource = parser.getsource()
  if recreatedsource != originalsource:
    print >>sys.stderr, "recreatedsource != originalsource"
  sys.stdout.write(recreatedsource)
  
  unpickled = pickle.loads(pickled)
  sys.stdout.write("===========================================\n")
  sys.stdout.write(unpickled.getsource())
  if unpickled.getsource() != recreatedsource:
    print >>sys.stderr, "unpickledsource != recreatedsource"

