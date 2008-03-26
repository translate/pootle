#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007 Zuza Software Foundation
# Copyright 2002, 2003 St James Software
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#


""" Handles indexing and searching the index
"""

import os, os.path
import time
import tempfile
from jToolkit import errors
from jToolkit.web.simplewebserver import ThreadLockWrap
from jToolkit.web import server
from jToolkit.web import postMultipart
from jToolkit import glock
import sys
import pickle
import threading
import time

def import_pylucene():
	try:
		import PyLucene
		return PyLucene, True
	except ImportError:
		# try again with "lucene" (for PyLucene v2.3)
		try:
			import lucene
			# pylucene v2.3 is not yet usable for us
			if lucene.VERSION >= "2.3.0":
				print "WARNING: PyLucene v2.3 is not yet supported. Skipping PyLucene ..."
				return None, False
				#lucene.initVM(lucene.CLASSPATH)
				## map "lucene" to "PyLucene" for easier coding
				#PyLucene = lucene
				#return lucene, True                            
		except:
			return None, False

def get_version_pylucene():
	if indexer.VERSION.startswith("1."):
		return 1
	else:
		return 2

def Occur(required, prohibited):
	if   required == True  and prohibited == False:
		return PyLucene.BooleanClause.Occur.MUST
	elif required == False and prohibited == False:
		return PyLucene.BooleanClause.Occur.SHOULD
	elif required == False and prohibited == True:
		return PyLucene.BooleanClause.Occur.MUST_NOT
	else:
		# It is an error to specify a clause as both required
		# and prohibited
		return None

class Wrapper:
	def __init__(self, **kwargs):
		for key, value in kwargs.iteritems():
			self.__dict__[key] = value

def ClassWrap(cls, **kwargs):
	for key, value in kwargs.iteritems():
		cls.__dict__[key] = value

class LupyWrapper:
	def __init__(self, lupy):
		self.lupy = lupy
		self.__version__ = lupy.__version__
		# for IndexReader.open
		self.IndexReader = Wrapper(open=self.openIndexReader)
		self.FSDirectory = Wrapper(getDirectory=self.lupy.store.getDirectory)
		self.Document = self.lupy.document.Document
		self.Field = self.lupy.document.Field
		self.Term = self.lupy.index.term.Term
		self.TermQuery = lupy.search.term.TermQuery
		class CallableInt(int):
			def __call__(self):
				return self
		class Hits(self.lupy.search.hits.Hits, object):
			def id(self, i):
				return self.hitDocs[i]["id"]
			def __iter__(self):
				for i in range(len(self)):
					yield i, self.doc(i)
			def getlength(self):
				return CallableInt(self._length)
			def setlength(self, newlength):
				self._length = newlength
			length = property(getlength, setlength)
		self.lupy.search.hits.Hits = Hits
		class BooleanQuery(self.lupy.search.boolean.BooleanQuery):
			def add(self, queryorclause, required=None, prohibited=None):
				"""Adds a BooleanClause or BooleanQuery to this query"""
				if isinstance(queryorclause, lupy.search.boolean.BooleanClause):
					return self.addClause(queryorclause)
				else:
					return lupy.search.boolean.BooleanQuery.add(self, queryorclause, required, prohibited)
		self.BooleanQuery = BooleanQuery
		self.BooleanClause = self.lupy.search.boolean.BooleanClause
		class QueryParser:
			def __init__(self, defaultFieldName, analyzer):
				self.defaultFieldName = defaultFieldName
				self.analyzer = analyzer
			def parseQuery(self, search, fieldName=None, analyzer=None):
				if analyzer is None:
					analyzer = self.analyzer
				if fieldName is None:
					fieldName = self.defaultFieldName
				tokens = list(analyzer(search))
				if len(tokens) == 1:
					term = indexer.Term(fieldName, tokens[0])
					query = indexer.TermQuery(term)
				else:
					tokensearches = [(fieldName, token) for token in tokens]
					query = indexer.BooleanQuery()
					for token in tokens:
						term = indexer.Term(fieldName, token)
						tokenquery = indexer.TermQuery(term)
						query.add(tokenquery, False, False)
				return query
			def parse(search, fieldName, analyzer):
				return QueryParser(fieldName, analyzer).parseQuery(search)
			parse = staticmethod(parse)
		self.QueryParser = QueryParser
	def StandardAnalyzer(self):
		return self.lupy.index.documentwriter.standardTokenizer
	def IndexSearcher(self, indexReader):
		indexSearcher = self.lupy.search.indexsearcher.IndexSearcher(indexReader.directory)
		# FIXME: Lupy seems to close the searcher and reader with its DIRECTORIES thing
		indexSearcher.native_close = indexSearcher.close
		def closesearcher():
			try:
				indexSearcher.native_close()
			except Exception, e:
				print "error closing searcher", e
				pass
		indexSearcher.close = closesearcher
		return indexSearcher
	def openIndexReader(self, storeDir):
		indexReader = self.lupy.search.indexsearcher.open(storeDir)
		indexReader.getCurrentVersion = indexReader.lastModified
		indexReader.deleteDocument = indexReader.doDelete
		indexReader.deleteDocuments = indexReader.deleteTerm
		indexReader.getFieldNames = indexReader.fieldNames
		# FIXME: Lupy seems to close the searcher and reader with its DIRECTORIES thing
		indexReader.native_close = indexReader.close
		def closereader():
			try:
				indexReader.native_close()
			except Exception, e:
				print "error closing reader", e
				pass
		indexReader.close = closereader
		return indexReader
	def IndexWriter(self, storeDir, analyzer, create):
		# the arguments are the other way round
		return self.lupy.index.indexwriter.IndexWriter(storeDir, create, analyzer)

def import_lupy():
	try:
		import lupy.index.documentwriter
		import lupy.index.indexwriter
		import lupy.index.term
		import lupy.search.indexsearcher
		import lupy.search.boolean
		import lupy.search.term
		import lupy.store
		import lupy.document
		return LupyWrapper(lupy), True
	except:
		return None, False

INDEXERS = {"PyLucene": import_pylucene, "lupy": import_lupy}

def use_indexer(indexer_name):
	import_function = INDEXERS[indexer_name]
	indexer_module, success = import_function()
	return indexer_module, success

def find_indexer(preferred_indexer):
	indexer_module, success = use_indexer(preferred_indexer)
	if success:
		return preferred_indexer, indexer_module, success
	for indexer in INDEXERS:
		if indexer == preferred_indexer:
			continue
		indexer_module, success = use_indexer(indexer)
		if success:
			return indexer, indexer_module, success
	return None, None, False

def init_module(preferred_indexer):
	modulevars = globals()
	indexer, indexer_module, success = find_indexer(preferred_indexer)
	modulevars[indexer] = indexer_module
	modulevars["INDEXER"] = indexer
	modulevars["indexer"] = indexer_module
	modulevars["HAVE_INDEXER"] = success

PREFERRED_INDEXER = "PyLucene"
INDEXER = None
init_module(PREFERRED_INDEXER)

# Here, we find out whether we're under mod_python or not
from jToolkit.web import safeapache
INSIDE_APACHE = not isinstance(safeapache.apache, safeapache.FakeApache)
defaulterrorhandler = errors.ConsoleErrorHandler()

# TODO: add forced unlocking using PyLucene.IndexReader.unlock(dirname) when lock errors occur and we have the glock

def StandardAnalyzer():
	return indexer.StandardAnalyzer()

class IndexerBase:
	"""base class to be inherited by all real implementations
	"""

	def __init__(self, config, analyzer=None, encoding=None, errorhandler=None):
		"""initialize the basic properties of an indexer

		@type config: objects
		@param config: must containt at least "indexdir" (location of the
			indexer database) and may contain a two-dimensional dictionary
			"types" describing available converters (see function
			'decodeContents' below)
		@type analyzer: object
		@param analyzer: defaults to "StandardAnalyzer"
		@type encoding: string
		@param encoding: defaults to "iso-8859-1"
		@type errorhandler: object
		@param errorhandler: defaults to jToolkit.ConsoleErrorHandler()
		"""
		if not HAVE_INDEXER:
			raise ImportError("Indexer not present (PyLucene or lupy)")
		if analyzer is None:
			analyzer = StandardAnalyzer()
		if encoding is None:
			encoding = 'iso-8859-1'
		if errorhandler is None:
			errorhandler = defaulterrorhandler
		self.analyzer = analyzer
		self.encoding = encoding
		self.errorhandler = errorhandler
		self.storeDir = config.indexdir
		lockname = os.path.join(tempfile.gettempdir(),self.storeDir.replace('/','_').replace('\\','_').replace(':','_'))
		self.dirLock = glock.GlobalLock(lockname)
		if not os.path.exists(self.storeDir):
			os.mkdir(self.storeDir)

		# This parses out a list of programs to use to decode contents
		self.types = {}
		if hasattr(config, "types"):
			for key, subtype in config.types.iteritems():
				firstPart = key
				for key2, value in subtype.iteritems():
					self.types[firstPart+"/"+key2] = value

	def indexFiles(self, fileNames, ID=None):
		"""real indexer implementations must override this function"""
		raise NotImplementedError("IndexerBase.indexFiles")

	def indexFields(self, fieldDicts):
		"""real indexer implementations must override this function"""
		raise NotImplementedError("IndexerBase.indexFields")

	def startIndex(self):
		"""real indexer implementations must override this function"""
		raise NotImplementedError("IndexerBase.startIndex")

	def commitIndex(self):
		"""real indexer implementations must override this function"""
		raise NotImplementedError("IndexerBase.commitIndex")

	def deleteIndex(self):
		"""real indexer implementations must override this function"""
		raise NotImplementedError("IndexerBase.deleteIndex")

	def decodeContents(self, contenttype, contents):
		"""check if an external converter is defined for the type and run it

		External converters may be defined when initializing the indexer class
		via the "config" argument. It may contain a dictionary "types"
		containing datasets like the following:
			{ "text": { "plain": "/usr/bin/plaintext_converter '$1' '$2'" } }
		The program '/usr/bin/plaintext_converter' reads the content of file
		'$1' and writes the converted output to '$2'.
		One or both parameters may be omitted - thus falling back to stdout
		respective stdin/stdout.

		@type contenttype: string
		@param contenttype: e.g. "text/plain"
		@type contents: string
		@param contents: the data to be converted
		@rtype: string
		@return: utf8-encoded string of converted input data
		"""
		if contenttype in self.types.keys():
			# Attempt to run the program
			# This will either require 1 temporary file (input),
			# 2 temporary files (input/output) or none (use stdin/stdout)
			inFileName = outFileName = None
			command = self.types[contenttype]
			if command.find('$1') != -1:
				inFile, inFileName = tempfile.mkstemp()
				command = command.replace('$1',inFileName)
				os.close(inFile)
				inFile = open(inFileName,'wb')
				inFile.write(contents)
				inFile.close()
			if command.find('$2') != -1:
				outFile, outFileName = tempfile.mkstemp()
				command = command.replace('$2',outFileName)
				os.close(outFile)
			try:
				myin, myout = os.popen2(command)
				if not inFileName:
					myin.write(contents)
				myin.close()
				if outFileName:
					outFile = open(outFileName,'rb')
					reply = outFile.read()
					outFile.close()
					os.remove(outFileName)
				else:
					reply = myout.read().decode('utf8','ignore')
				if inFileName:
					os.remove(inFileName)
				return reply
			except:
				# TODO: narrow this 'except' down to OSError
				self.errorhandler.logerror("Could not run command specified for content-type %s. Command = %s"
						% (contenttype, command))
				return None
		else:
			return None

class PerFieldAnalyzer(object):
	"""Used for handling analysis of different fields"""
	def __init__(self, analyzerslist, defaultanalyzer=None):
		"""construct the Analyzer using the given ones"""
		if defaultanalyzer is None:
			defaultanalyzer = StandardAnalyzer()
		self.analyzers = {}
		self.defaultanalyzer = defaultanalyzer
		for fieldname, analyzer in analyzerslist:
			self.analyzers[fieldname] = analyzer
	def getAnalyzer(self, fieldName):
		return self.analyzers.get(fieldName, self.defaultanalyzer)
	def tokenStream(self, fieldName, reader):
		"""tokenStream method for PyLucene"""
		return self.getAnalyzer(fieldName).tokenStream(fieldName, reader)
	def __call__(self, val):
		"""call method for Lupy"""
		return self.defaultanalyzer(val)

class ExactAnalyzer(object):
	def tokenStream(self, fieldName, reader):
		"""tokenStream method for PyLucene"""
		input = reader.read()
		return iter([indexer.Token(input, 0, len(input)), None])
	def __call__(self, string):
		"""call method for Lupy"""
		return [string]

class Indexer(IndexerBase):
	"""Used for handling the indexing side of things"""

	def __init__(self, config, analyzer=None, encoding=None, errorhandler=None):
		if not HAVE_INDEXER:
			raise ImportError("Indexer not present (PyLucene or lupy)")
		IndexerBase.__init__(self, config, analyzer, encoding, errorhandler)
		self.writer = None
		try:
			tempreader = indexer.IndexReader.open(self.storeDir)
			tempreader.close()
			self.createdIndex = False
		except Exception, e:
			# Write an error out, in case this is a real problem instead of an absence of an index
			errorstr = str(e).strip() + "\n" + self.errorhandler.traceback_str()
			self.errorhandler.logerror("could not open index, so going to create, error follows: " + errorstr)
			# Create the index, so we can open cached readers on it
			tempwriter = indexer.IndexWriter(self.storeDir, self.analyzer, True)
			tempwriter.close()
			self.createdIndex = True

	def __del__(self):
		self.close()

	def close(self):
		if self.writer:
			self.writer.close()
			self.writer = None
		self.dirLock.forcerelease()

	def indexFiles(self, fileNames, ID=None):
		if self.writer is None:
			self.errorhandler.logerror("indexer: indexFiles called without initialising the writer")
			return False
		for file in fileNames:
			fp = open(file)
			contents = unicode(fp.read(), self.encoding)
			fp.close()
			doc = indexer.Document()
			if get_version_pylucene() == 1:
				doc.add(indexer.Field("file_name",
						os.path.basename(file), True, True, True))
			else:
				doc.add(indexer.Field("file_name", os.path.basename(file),
						PyLucene.Field.Store.YES,
						PyLucene.Field.Index.TOKENIZED))
			if len(contents) > 0:
				if get_version_pylucene() == 1:
					doc.add(indexer.Field("file_contents", contents,
							True, True, True))
				else:
					doc.add(indexer.Field("file_contents", contents,
							PyLucene.Field.Store.YES,
							PyLucene.Field.Index.TOKENIZED))
			if ID is not None:
				if get_version_pylucene() == 1:
					doc.add(indexer.Field("recordID", ID, True, True, True))
				else:
					doc.add(indexer.Field("recordID", ID,
							PyLucene.Field.Store.YES,
							PyLucene.Field.Index.TOKENIZED))
			self.writer.addDocument(doc)
			self.errorhandler.logtrace("indexer: Indexing file %s" % file)

	def indexFields(self, fieldDicts):
		""" fieldDicts should be an array of dictionaries
		Each dictionary should be searchField:fieldContents in structure"""
		if self.writer is None:
			self.errorhandler.logerror("indexer: indexFields called without initialising the writer")
			return False
		if type(fieldDicts) == dict:
			fieldDicts = [fieldDicts]
		for fieldSet in fieldDicts:
			doc = indexer.Document()
			for field in fieldSet.keys():
				value = fieldSet[field]
				if isinstance(value, str):
					try:
						value = value.decode("UTF-8")
					except UnicodeDecodeError, e:
						self.errorhandler.logtrace("error decoding field %s: %s; using charmap to decode (value %r)" % (field, e, e))
						value = value.decode("charmap")
				if not isinstance(value, (str, unicode)):
					value = str(value)
				if get_version_pylucene() == 1:
					doc.add(indexer.Field(str(field), value, True, True, True))
				else:
					doc.add(indexer.Field(str(field), value,
							PyLucene.Field.Store.YES,
							PyLucene.Field.Index.TOKENIZED))
			self.writer.addDocument(doc)

	def startIndex(self):
		"""starts index writing. must be followed by commitIndex or will leave index locked"""
		try:
			tempreader = indexer.IndexReader.open(self.storeDir)
			tempreader.close()
			create = False
		except Exception, e:
			self.errorhandler.logerror("store missing, need to create: %s" % self.errorhandler.traceback_str())
			create = True
#		if self.dirLock.isLocked():
#			raise Exception("This should never happen with one client")
		self.dirLock.acquire()
		try:
			self.writer = indexer.IndexWriter(self.storeDir, self.analyzer, create)
			if get_version_pylucene() == 1:
				self.writer.maxFieldLength = 1048576
			else:
				self.writer.setMaxFieldLength(1048576)
			success = True
		except Exception,e:
			self.errorhandler.logerror("Failed to create index.  %s" % self.errorhandler.traceback_str())
			success = False
		return success

	def commitIndex(self, optimize=True):
		"""closes the index (optimizing if required), and unlocks it"""
		if self.writer is None:
			self.errorhandler.logerror("commitIndex called without successful startIndex")
		else:
			try:
				if optimize:
					self.writer.optimize()
			finally:
				self.writer.close()
				self.writer = None
		self.dirLock.release()

	def optimizeIndex(self):
		"""optimizes the index by starting and committing"""
		self.startIndex()
		self.commitIndex()

	def deleteIndex(self):
		self.dirLock.acquire()
		numtries = 0
		ret = True
		while numtries < 10:
			try:
				numtries += 1
				store = indexer.FSDirectory.getDirectory(self.storeDir, True)
				store.close()
				break
			except Exception,e:
				if numtries < 10:
					time.sleep(0.01)
				else:
					self.errorhandler.logerror("Could not delete index: " + str(e))
					ret = False
		self.dirLock.release()
		return ret

	def isNewIndex(self):
		"""Returns True if this indexer just created the index at the stated directory"""
		return self.createdIndex

class Searcher:
	def __init__(self, storeDir, analyzer=None, errorhandler=None):
		"""Construct a searcher. this requires a lock, so cannot be done while the index is being written to"""
		if not HAVE_INDEXER:
			raise ImportError("Indexer not present (PyLucene or lupy)")
		if analyzer is None:
			analyzer = StandardAnalyzer()
		if errorhandler is None:
			errorhandler = defaulterrorhandler
		self.analyzer = analyzer
		self.errorhandler = errorhandler
		self.storeDir = storeDir
		self.indexReader = self.indexVersion = self.indexSearcher = None
		lockname = os.path.join(tempfile.gettempdir(),self.storeDir.replace('/','_').replace('\\','_').replace(':','_'))
		self.dirLock = glock.GlobalLock(lockname)
		# if we can't acquire the lock, someone is busy writing, and we should wait for them
		self.dirLock.acquire(blocking=True)
		numtries = 0
		# windows file locking seems inconsistent, so we try 10 times
		try:
			while numtries < 10:
				numtries += 1
				try:
					self.indexReader = indexer.IndexReader.open(self.storeDir)
					self.indexVersion = self.indexReader.getCurrentVersion(self.storeDir)
					self.indexSearcher = indexer.IndexSearcher(self.indexReader)
					numtries = 10
				except Exception, e:
					self.errorhandler.logtrace("exception trying to open index: " + str(e))
					if numtries >= 10:
						self.errorhandler.logerror("failed to open index after 10 tries")
						raise
					self.errorhandler.logtrace("sleeping and then trying to open index again")
					time.sleep(0.01)
					continue
		finally:
			self.dirLock.release()

	def __del__(self):
		self.close()

	def searchField(self, fieldName, search, returnedFieldChoices):
		"""searches the given fieldName with the given search string, returning required fields
		returnedFieldChoices is a tuple of valid combinations of fields to return (each of which is a list)
		for simplicity you can also give a single string that is a field choice or a single list of fields"""
		if get_version_pylucene() == 1:
			query = indexer.QueryParser.parse(search, fieldName, self.analyzer)
		else:
			query = indexer.QueryParser(fieldName, self.analyzer).parse(search)
		return self.search(query, returnedFieldChoices)

	def searchFields(self, fieldSearches, returnedFieldChoices, requireall=False):
		"""searches all the given (fieldName, search string) fieldSearches, returning required fields
		returnedFieldChoices is a tuple of valid combinations of fields to return (each of which is a list)
		for simplicity you can also give a single string that is a field choice or a single list of fields"""
		combinedquery = self.makeQuery(fieldSearches, requireall)
		return self.search(combinedquery, returnedFieldChoices)

	def makeQuery(self, fieldSearches, requireall):
		"""combines the given (fieldName, search string) fieldSearches (or queries)"""
		combinedquery = indexer.BooleanQuery()
		for fieldSearch in fieldSearches:
			if isinstance(fieldSearch, indexer.BooleanQuery):
				if get_version_pylucene() == 1:
					clause = indexer.BooleanClause(fieldSearch,
							requireall, False)
				else:
					clause = indexer.BooleanClause(fieldSearch,
							Occur(requireall, False))
				combinedquery.add(clause)
			elif isinstance(fieldSearch, tuple):
				fieldName, search = fieldSearch
				analyzer = self.analyzer
				if isinstance(analyzer, PerFieldAnalyzer):
					analyzer = analyzer.getAnalyzer(fieldName)
				if get_version_pylucene() == 1:
					query = indexer.QueryParser.parse(search, fieldName, analyzer)
					combinedquery.add(query, requireall, False)
				else:
					query = indexer.QueryParser(fieldName,analyzer).parse(search)
					combinedquery.add(query, Occur(requireall, False))
			else:
				raise ValueError("unexpected value in fieldSearch: %r" % fieldSearch)
		return combinedquery

	def notQuery(self, query):
		"""returns a query that matches everything but the query"""
		notquery = indexer.BooleanQuery()
		if get_version_pylucene() == 1:
			clause = indexer.BooleanClause(query, False, True)
		else:
			clause = indexer.BooleanClause(query, Occur(False, True))
		notquery.add(clause)
		return notquery

	def searchAllFields(self, search, returnedFieldChoices):
		"""searches all the fields with the same search string, returning required fields
		returnedFieldChoices is a tuple of valid combinations of fields to return (each of which is a list)
		for simplicity you can also give a single string that is a field choice or a single list of fields"""
		fields = self.getFields()
		return self.searchFields([(field, search) for field in fields], returnedFieldChoices)

	def getFields(self):
		"""returns a list of all the field names in the index"""
		self.checkVersion()
		return self.indexReader.getFieldNames()

	def search(self, query, returnedFieldChoices=None):
		"""returns the result of a search using a native indexer query
		if given, returnedFieldChoices is a tuple of valid combinations of fields to return (each of which is a list)
		for simplicity you can also give a single string that is a field choice or a single list of fields"""
		self.checkVersion()
		hits = self.indexSearcher.search(query)
		if returnedFieldChoices is not None:
			results = self.extractFieldsFromSearch(hits, returnedFieldChoices)
			return results
		return hits

	def close(self):
		"""closes the searcher if still open"""
		if self.indexSearcher:
			self.indexSearcher.close()
			self.indexSearcher = None
		if self.indexReader:
			self.indexReader.close()
			self.indexReader = None

	def checkVersion(self):
		"""checks that we've got the latest version of the index"""
		try:
			self.dirLock.acquire(blocking=False)
		except glock.GlobalLockError, e:
			# if this fails the index is being rewritten, so we continue with our old version
			return
		try:
			if self.indexReader is None or self.indexSearcher is None:
				self.indexReader = indexer.IndexReader.open(self.storeDir)
				self.indexSearcher = indexer.IndexSearcher(self.indexReader)
			elif self.indexVersion != self.indexReader.getCurrentVersion(self.storeDir) or INDEXER == "lupy":
				self.indexSearcher.close()
				self.indexReader.close()
				self.indexReader = indexer.IndexReader.open(self.storeDir)
				self.indexSearcher = indexer.IndexSearcher(self.indexReader)
				self.indexVersion = self.indexReader.getCurrentVersion(self.storeDir)
		except Exception,e:
			self.errorhandler.logerror("Error attempting to read index - try reindexing: "+str(e))
		self.dirLock.release()

	def extractFieldsFromSearch(self, hits, returnedFieldChoices):
		"""This function takes a list of hits and a list of field choices.
		The idea of field choices is that you want to retrieve certain fields from the search results
		and, if they're not there, retrieve another set of fields, etc.
		returnedFieldChoices is a tuple of valid combinations of fields to return (each of which is a list)
		for simplicity you can also give a single string that is a field choice or a single list of fields"""
		if isinstance(returnedFieldChoices, (list, basestring)):
			returnedFieldChoices = (returnedFieldChoices,)
		results = []
		for hit, doc in hits:
			if self.indexReader.isDeleted(hits.id(hit)):
				continue
			for setOfFields in returnedFieldChoices:
				fields = self.extractFieldFromDoc(doc, setOfFields)
				if not fields is None:
					results.append(fields)
					break

		return results

	def extractFieldFromDoc(self, doc, setOfFields):
		"""returns a dictionary with the values of all the fields given in setOfFields
		for simplicity, setOfFields can also be a string with one field name"""
		if isinstance(setOfFields, basestring):
			setOfFields = [setOfFields]
		fields = {}
		for field in setOfFields:
			fields[field] = doc.get(field)
			if fields[field] is None:
				return None
		return fields

	def deleteDoc(self, fieldSearches, exactmatch=True):
		"""takes the fieldSearches and deletes documents whose fields match the given values
		returns the number of documents deleted or False if indexReader not open
		if exact match is set, then fieldSearches must be tuples of keys, values (not queries)"""
		self.checkVersion()
		if isinstance(fieldSearches, dict):
			fieldSearches = fieldSearches.items()
		if not self.indexReader:
			return False
		self.dirLock.acquire()
		try:
			# short cut for a single term search
			if isinstance(fieldSearches, list) and len(fieldSearches) == 1 and isinstance(fieldSearches[0], tuple):
				keyfield, keyvalue = fieldSearches[0]
				term = indexer.Term(keyfield, keyvalue)
				numdeletes = self.indexReader.deleteDocuments(term)
			else:
				if not isinstance(fieldSearches, list):
					query = fieldSearches
				else:
					query = self.makeQuery(fieldSearches, requireall=True)
				hits = self.search(query)
				numdeletes = 0
				hitcount = hits.length()
				for i in range(hitcount):
					found = True
					# check the values match exactly (no analyzers involved)
					if exactmatch and isinstance(fieldSearches, list):
						doc = hits.doc(i)
						for fieldSearch in fieldSearches:
							if not isinstance(fieldSearch, tuple):
								continue
							keyname, keyvalue = fieldSearch
							if doc.get(keyfield) != keyvalue:
								found = False
								break
					if found:
						docid = hits.id(i)
						self.indexReader.deleteDocument(docid)
						numdeletes += 1
			if numdeletes:
				# Close and reopen our reader to commit the delete
				self.indexSearcher.close()
				self.indexReader.close()
				self.indexReader = indexer.IndexReader.open(self.storeDir)
				self.indexSearcher = indexer.IndexSearcher(self.indexReader)
		finally:
			self.dirLock.release()
		return numdeletes

	def getModifyDoc(self, IDFields, modifiedFields):
		# This function removes a document, and returns its fields, modified as indicated, in a dict
		# since we can't modify directly, but need to delete a doc and then readd it
		query = indexer.BooleanQuery()
		analyzer = indexer.StandardAnalyzer()
		for keyfield in IDFields.keys():
			if get_version_pylucene() == 1:
				query.add(indexer.QueryParser.parse(IDFields[keyfield], keyfield, analyzer), True, False)
			else:
				query.add(indexer.QueryParser.parse(IDFields[keyfield], keyfield, analyzer), Occur(True, False))
		hits = self.search(query)
		modifiedFields.update(IDFields)
		for hit, doc in hits:
			for field in doc.fields():
				if not modifiedFields.has_key(field.name()):
					modifiedFields[field.name()] = field.stringValue()
		self.deleteDoc(IDFields)
		return modifiedFields

class SearcherPool:
	"""Pools Searchers in a thread-safe manner, and so allows optimised index searching"""
	def __init__(self, errorhandler=None):
		if errorhandler is None:
			errorhandler = defaulterrorhandler
		self.errorhandler = errorhandler

		self.availableSearchers = {}
		self.lockedSearchers = {}
		self.searcherLock = threading.Lock()
		self.inshutdown = 0

	def searchField(self, storeDir, fieldName, search, returnedFieldChoices):
		if self.inshutdown:
			return False
		searcher = self.getSearcher(storeDir)
		result = searcher.searchField(fieldName, search, returnedFieldChoices)
		self.returnSearcher(storeDir, searcher)
		return result

	def getFields(self, storeDir):
		if self.inshutdown:
			return False
		searcher = self.getSearcher(storeDir)
		result = searcher.getFields()
		self.returnSearcher(storeDir, searcher)
		return result

	def searchAllFields(self, storeDir, search, returnedFieldChoices):
		if self.inshutdown:
			return False
		searcher = self.getSearcher(storeDir)
		result = searcher.searchAllFields(search, returnedFieldChoices)
		self.returnSearcher(storeDir, searcher)
		return result

	def deleteDoc(self, storeDir, uniqueIDs):
		if self.inshutdown:
			return False
		searcher = self.getSearcher(storeDir)
		result = searcher.deleteDoc(uniqueIDs)
		self.returnSearcher(storeDir, searcher)
		return result

	def getModifyDoc(self, storeDir, IDFields, modifiedFields):
		if self.inshutdown:
			return False
		searcher = self.getSearcher(storeDir)
		result = searcher.getModifyDoc(IDFields, modifiedFields)
		self.returnSearcher(storeDir, searcher)
		return result

	def getSearcher(self, storeDir):
		self.searcherLock.acquire()
		searcher = None
		if not self.availableSearchers.has_key(storeDir):
			self.availableSearchers[storeDir] = []
			searcher = Searcher(storeDir, errorhandler=self.errorhandler)
			self.lockedSearchers[storeDir] = [searcher]
		else:
			if self.availableSearchers[storeDir] == []:
				searcher = Searcher(storeDir, errorhandler=self.errorhandler)
			else:
				searcher = self.availableSearchers[storeDir].pop()
			if not self.lockedSearchers.has_key(storeDir):
				self.lockedSearchers[storeDir] = [searcher]
			else:
				self.lockedSearchers[storeDir].append(searcher)
		self.searcherLock.release()
		return searcher

	def returnSearcher(self, storeDir, searcher):
		self.searcherLock.acquire()
		if self.lockedSearchers.has_key(storeDir):
			if searcher in self.lockedSearchers[storeDir]:
				self.lockedSearchers[storeDir].pop(self.lockedSearchers[storeDir].index(searcher))

		if self.availableSearchers.has_key(storeDir):
			if searcher not in self.availableSearchers[storeDir]:
				self.availableSearchers[storeDir].append(searcher)

		self.searcherLock.release()

	def close(self, storeDir):
		if not self.availableSearchers.has_key(storeDir):
			return True
		self.searcherLock.acquire()
		while len(self.lockedSearchers[storeDir]) > 0:
			if len(self.lockedSearchers[storeDir]) == 0:
				del self.lockedSearchers[storeDir]

			self.searcherLock.release()
			time.sleep(0.1)
			self.searcherLock.acquire()

		for searcher in self.availableSearchers[storeDir]:
			searcher.close()
		self.searcherLock.release()

	def closeAll(self):
		self.searcherLock.acquire()
		self.inshutdown = 1
		while len(self.lockedSearchers) > 0:
			for key in self.lockedSearchers:
				if len(self.lockedSearchers[key]) == 0:
					del self.lockedSearchers[key]

			self.searcherLock.release()
			time.sleep(0.1)
			self.searcherLock.acquire()

		for key in self.availableSearchers:
			for searcher in self.avaiableSearchers[key]:
				searcher.close()

		self.searcherLock.release()

class ChildIndexServer(server.AppServer):
	name = "ChildIndexServer"
	class EmptyObject:
		pass

	def __init__(self, instance, webserver=None, sessioncache=None, errorhandler=None):
		server.AppServer.__init__(self, instance, webserver, sessioncache, errorhandler)
		self.activeIndexers = {}
		self.directoryLocks = {}
		self.searcherPool = SearcherPool(self.errorhandler)

	def __del__(self):
		"""An attempt at a clean-up function"""
		self.searcherPool.close()
		self.closeOpenIndexers()

	def getpage(self, pathwords, session, argdict):
		if len(pathwords) == 2:
			try:
				if pathwords[0] == "index":
					reply = self.indexCommand(pathwords[1], argdict)
				elif pathwords[0] == 'search':
					reply = self.searchCommand(pathwords[1], argdict)
				else:
					errorstr = 'error: Could not find path %s' % "/".join(pathwords)
					reply = errorstr
					self.errorhandler.logerror(errorstr)
			except Exception, e:
				reply = 'error: %s' % e
				self.errorhandler.logerror("error broke index service: %s" % self.errorhandler.traceback_str())
			return reply
		return 404

	def indexCommand(self, command, argdict):
		"""Arguments: command threadID,args"""
		if not argdict.has_key("threadID"):
			self.errorhandler.logerror("Indexing requires threadID as an argument")
			return "error: Indexing requires threadID as an argument"

		threadID = argdict["threadID"]
		if command not in ['indexFiles','indexFields','startIndex','commitIndex','deleteIndex','isNewIndex']:
			errorstr = "Command %s for the indexer not recognised" % command
			self.errorhandler.logerror(errorstr)
			return "error: "+errorstr

		if argdict.has_key("command_args"):
			args = pickle.loads(str(argdict["command_args"]))
			if type(args) != type(()):
				self.errorhandler.logerror("pickled args should be of type tuple")
				return "error: pickled args should be of type tuple"
		else:
			args = ()

		try:
			if command == 'startIndex':
				return self.indexStartIndex(threadID, args)
			elif command == 'commitIndex':
				return self.indexCommitIndex(threadID, args)
			elif command == 'deleteIndex':
				return self.indexDeleteIndex(threadID, args)
			elif command == 'indexFiles':
				return self.indexIndexFiles(threadID, args)
			elif command == 'indexFields':
				return self.indexIndexFields(threadID, args)
			elif command == 'isNewIndex':
				return self.indexIsNewIndex(threadID, args)
		except Exception, message:
			errorstr = str(message).strip()+" / ".join(self.errorhandler.traceback_str().split("\n"))
			self.errorhandler.logerror(errorstr)
			return "error: "+errorstr

		self.errorhandler.logerror("error: Reached unreachable condition")
		return "error: Reached unreachable condition"

	def indexStartIndex(self, threadID, args):
		if len(args) != 1:
			errorstr = "index.startIndex takes exactly 1 argument (storageDir) (given %r)" % (args,)
			self.errorhandler.logerror(errorstr)
			return "error: "+errorstr

		self.indexInitialiseThread(args[0], threadID)

		ret = self.activeIndexers[threadID].startIndex()
		return str(ret)

	def indexCommitIndex(self, threadID, args):
		if len(args) != 0:
			self.errorhandler.logerror("index.commitIndex takes no arguments")
			return "error: index.commitIndex takes no arguments"

		if not self.activeIndexers.has_key(threadID):
			self.errorhandler.logerror("index.commitIndex attempted on a thread with no open index")
			return "error: index.commitIndex attempted on a thread with no open index"

		ret = self.activeIndexers[threadID].commitIndex()
		# Should we be deleting and recreating this, or is this fine?
		return str(ret)

	def indexDeleteIndex(self, threadID, args):
		if len(args) != 1:
			self.errorhandler.logerror("index.deleteIndex takes exactly 1 argument (storageDir)")
			return "error: index.deleteIndex takes exactly 1 argument (storageDir)"

		self.indexInitialiseThread(args[0], threadID)

		ret = self.activeIndexers[threadID].deleteIndex()
		return str(ret)

	def indexIndexFiles(self, threadID, args):
		if len(args) != 1 and len(args) != 2:
			self.errorhandler.logerror("index.indexFiles takes 1 or 2 arguments (fileNames, ID=None)")
			return "error: index.indexFiles takes 1 or 2 arguments (fileNames, ID=None)"

		fileNames = args[0]
		if len(args) == 2:
			ID = args[1]
		else:
			ID = None

		if not self.activeIndexers.has_key(threadID):
			self.errorhandler.logerror("index.indexFiles attempted on thread %s with no open index" % threadID)
			return "error: index.indexFiles attempted on thread %s with no open index" % threadID

		ret = self.activeIndexers[threadID].indexFiles(fileNames, ID)
		return str(ret)

	def indexIndexFields(self, threadID, args):
		if len(args) != 1:
			self.errorhandler.logerror("index.indexFields takes exactly 1 argument (fieldDicts)")
			return "error: index.indexFields takes exactly 1 argument (fieldDicts)"

		if not self.activeIndexers.has_key(threadID):
			self.errorhandler.logerror("index.indexFields attempted on thread %s with no open index" % threadID)
			return "error: index.indexFields attempted on thread %s with no open index" % threadID

		ret = self.activeIndexers[threadID].indexFields(args[0])
		return str(ret)

	def indexIsNewIndex(self, threadID, args):
		if len(args) != 1:
			self.errorhandler.logerror("index.isNewIndex takes exactly 1 argument (storageDir)")
			return "error: index.isNewIndex takes exactly 1 argument (storageDir)"

		self.indexInitialiseThread(args[0], threadID)

		ret = self.activeIndexers[threadID].isNewIndex()
		return str(ret)

	def indexInitialiseThread(self, indexdir, threadID):
		if not self.activeIndexers.has_key(threadID) or self.activeIndexers[threadID].storeDir != indexdir:
			config = self.EmptyObject()
			config.indexdir = indexdir
			self.activeIndexers[threadID] = Indexer(config, errorhandler=self.errorhandler)

	def searchCommand(self, command, argdict):
		if command not in ['searchField','getFields','searchAllFields','deleteDoc','getModifyDoc', 'close']:
			self.errorhandler.logerror("Command %s for the searcher not recognised" % command)
			return "error: Command %s for the searcher not recognised" % command

		if argdict.has_key("command_args"):
			args = pickle.loads(str(argdict["command_args"]))
			if type(args) != type(()):
				self.errorhandler.logerror("pickled args should be of type tuple")
				return "error: pickled args should be of type tuple"
		else:
			args = ()

		try:
			if command == 'searchField':
				reply = self.searchSearchField(args)
			elif command == 'getFields':
				reply = self.searchGetFields(args)
			elif command == 'searchAllFields':
				reply = self.searchSearchAllFields(args)
			elif command == 'deleteDoc':
				reply = self.searchDeleteDoc(args)
			elif command == 'getModifyDoc':
				reply = self.searchModifyDoc(args)
			elif command == 'close':
				reply = self.searchClose(args)
			else:
				self.errorhandler.logerror("reached unreachable condition")
				return "error: reached unreachable condition"
		except Exception, message:
			errorstr = "error: "+str(message).strip()+" / ".join(self.errorhandler.traceback_str().split("\n"))
			self.errorhandler.logerror(errorstr)
			return errorstr

		if type(reply) == type("") and reply.startswith("error"):
			return reply
		try:
			replystr = pickle.dumps(reply)
		except:
			errorstr = "error: Pickling error with object "+repr(reply) 
			self.errorhandler.logerror(self.errorhandler.traceback_str())
			return errorstr
		reply = str(len(replystr)) + "\n" + replystr
		return reply

	def searchSearchField(self, args):
		if len(args) != 4:
			self.errorhandler.logerror("search.searchField takes exactly 4 arguments (storeDir, fieldName, searchTerm, returnedFieldChoices)")
			return "error: search.searchField takes exactly 4 arguments (storeDir, fieldName, searchTerm, returnedFieldChoices)"

		storeDir, fieldName, searchTerm, returnedFieldChoices = args
		return self.searcherPool.searchField(storeDir, fieldName, searchTerm, returnedFieldChoices)

	def searchGetFields(self, args):
		if len(args) != 1:
			self.errorhandler.logerror("search.getFields takes exactly 1 argument (storeDir)")
			return "error: search.getFields takes exactly 1 argument (storeDir)"

		return self.searcherPool.getFields(args[0])

	def searchSearchAllFields(self, args):
		if len(args) != 3:
			self.errorhandler.logerror("search.searchAllFields takes exactly 3 arguments (storeDir, searchTerm, returnedFieldChoices)")
			return "error: search.searchAllFields takes exactly 3 arguments (storeDir, searchTerm, returnedFieldChoices)"

		storeDir, searchTerm, returnedFieldChoices = args
		return self.searcherPool.searchAllFields(storeDir, searchTerm, returnedFieldChoices)

	def searchDeleteDoc(self, args):
		if len(args) != 2:
			self.errorhandler.logerror("search.deleteDoc takes exactly 2 arguments (storeDir, uniqueIDs)")
			return "error: search.deleteDoc takes exactly 2 arguments (storeDir, uniqueIDs)"

		storeDir, uniqueIDs = args
		return self.searcherPool.deleteDoc(storeDir, uniqueIDs)

	def searchModifyDoc(self, args):
		if len(args) != 3:
			self.errorhandler.logerror("search.getModifyDoc takes exactly 2 arguments (storeDir, IDFields, modifiedFields)")
			return "error: search.getModifyDoc takes exactly 2 arguments (storeDir, IDFields, modifiedFields)"

		storeDir, IDFields, modifiedFields = args
		return self.searcherPool.getModifyDoc(storeDir, IDFields, modifiedFields)

	def searchClose(self, args):
		if len(args) != 1:
			self.errorhandler.logerror("search.close takes exactly 1 argument (storeDir)")
			return "error: search.getFields takes exactly 1 argument (storeDir)"

		return self.searcherPool.close(args[0])

	def closeOpenIndexers(self):
		for threadID in self.activeIndexers:
			indexer = self.activeIndexers[threadID]
			indexer.dirLock.lock()
			del self.activeIndexers[threadID]

class ApacheIndexer(IndexerBase):
	def __init__(self, config, analyzer=None, encoding=None, errorhandler=None):
		if not INSIDE_APACHE:
			raise Exception("ApacheIndexer was used while not running under mod_python")

		# Working on the theory that this will only be used on one thread
		# But we need to cache the name, because the actual thread being used will
		# be changed by Apache
		self.threadName = threading.currentThread().getName()
		IndexerBase.__init__(self, config, analyzer, encoding, errorhandler)

	def indexFiles(self, fileNames, ID=None):
		reply = self.runCommand("indexFiles",(fileNames,ID))
		if reply == False:
			return False
		return True

	def indexFields(self, fieldDicts):
		reply = self.runCommand("indexFields",(fieldDicts,))
		if reply == False:
			return False
		return True

	def startIndex(self):
		reply = self.runCommand("startIndex",(self.storeDir,))
		if reply == False:
			return False
		return True

	def commitIndex(self):
		reply = self.runCommand("commitIndex",())
		if reply == False:
			return False
		return True

	def deleteIndex(self):
		reply = self.runCommand("deleteIndex",(self.storeDir,))
		if reply == False:
			return False
		return True

	def isNewIndex(self):
		reply = self.runCommand("isNewIndex",(self.storeDir,))
		if reply == False:
			return False
		else:
			return True

	def runCommand(self, command, args):
		argdump = pickle.dumps(args)
		try:
			reply = postMultipart.post_multipart("localhost:"+str(separateProcessPort),"index/"+command,[('command_args',argdump),('threadID',self.threadName)],[])
			if len(reply) == 3:
				reply = reply[0]
			if reply[:5] == "error":
				self.errorhandler.logerror(reply[6:])
				raise IOError("Error in child process: "+reply[6:])
				return False
			if reply == "False":
				return False
			return reply
		except Exception, message:
			self.errorhandler.logerror("Error during ApacheIndexer running: "+str(message))

class ApacheSearcher:
	def __init__(self, storeDir, analyzer=None, errorhandler=None):
		if not INSIDE_APACHE:
			raise Exception("ApacheSearcher was used while not running under mod_python")
		self.storeDir = storeDir
		if errorhandler == None:
			errorhandler = defaulterrorhandler
		self.errorhandler = errorhandler
		if analyzer != None:
			self.errorhandler.logtrace("Warning: ApacheSearcher initialised with non-standard analyzer, which will be ignored")

	def close(self):
		return self.runCommand("close", ())

	def searchField(self, fieldName, search, returnedFieldChoices):
		return self.runCommand("searchField", (fieldName, search, returnedFieldChoices))

	def searchAllFields(self, search, returnedFieldChoices):
		return self.runCommand("searchAllFields", (search, returnedFieldChoices))

	def getFields(self):
		return self.runCommand("getFields", ())

	def deleteDoc(self, uniqueIDs):
		return self.runCommand("deleteDoc", (uniqueIDs,))

	def getModifyDoc(self, IDFields, modifiedFields):
		return self.runCommand("getModifyDoc", (IDFields, modifiedFields))

	def runCommand(self, command, args):
		"""Access the simplewebserver-run searcher, port denoted by separateProcessPort"""
		args = (self.storeDir,) + args
		argdump = pickle.dumps(args)
		try:
			# Access the simplewebserver here
			# We need to send one argument, command_args, containing the tuple of the args
			reply = postMultipart.post_multipart("localhost:"+str(separateProcessPort),"search/" + command, [("command_args",argdump)],[])
			if reply[0].startswith("error"):
				self.errorhandler.logerror(reply[0][6:])
				raise IOError("Error in child process: "+reply[0][6:])
				return False
			if reply[0].strip() == "False":
				return False
			reply = reply[0].strip()
			if reply.split("\n")[0].isdigit():
				reply = pickle.loads(reply.split("\n",1)[1])
			else:
				reply = None
			return reply
		except Exception, message:
			self.errorhandler.logerror("Error during ApacheSearcher running: "+str(message))

class GUIErrorHandler(errors.ErrorHandler):
	def __init__(self):
		try:
			import win32gui
			self.messagebox = lambda title, message: win32gui.MessageBox(0, message, title, 0)
		except ImportError:
			import wx
			wx.PyApp()
			self.messagebox = lambda title, message: wx.MessageBox(message, title)

	def showmessage(self, message):
		if "\n" in message:
			title = message[:message.find("\n")]
		else:
			title = message
		self.messagebox(title, message)
		return

	def logerror(self, message):
		self.showmessage(message)

	def logtrace(self, message):
		pass

def LaunchIndexProcess():
	"""This function sets up the module to run under Apache"""
	pythonexe = sys.executable
	if sys.platform == 'win32':
		for parentdir in (sys.prefix, sys.exec_prefix):
			testexec = os.path.join(parentdir, "python.exe")
			if os.path.exists(testexec):
				pythonexe = testexec
				break

		# Find a port
		import socket
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
		sock.bind(('',0))
		sock.listen(socket.SOMAXCONN)
		ipaddr, globals()['separateProcessPort'] = sock.getsockname()
		sock.close()
		separateProcessID = os.spawnl(os.P_NOWAIT,pythonexe,"python.exe",os.path.abspath(__file__),"--port",str(separateProcessPort),"--watchpid",str(os.getpid()))
		globals()['Indexer'] = ApacheIndexer
		globals()['Searcher'] = ApacheSearcher

if INSIDE_APACHE:
	# We're running under Apache
	LaunchIndexProcess()

if __name__ == '__main__':
	from jToolkit.web import simplewebserver
	parser = simplewebserver.WebOptionParser()
	options, args = parser.parse_args()
	baseserver = dict(simplewebserver.servertypes)[options.servertype]
	webserverclass = simplewebserver.jToolkitHTTPServer(baseserver)
	class instance:
		errorfile = "indexing-errors.log"
		tracefile = "indexing-errors.log"
		name = "Indexing web service"
	# guierrorhandler = GUIErrorHandler()
	httpd = webserverclass(options, defaulterrorhandler)
	server = ChildIndexServer(instance, httpd)
	simplewebserver.run(server, options)

