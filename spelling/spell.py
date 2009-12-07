#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007 Zuza Software Foundation, WordForge Foundation
#
# This is free software; you can redistribute it and/or modify
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""A Spell Checking server protocol framework

This protocol framework starts with Google spell checker protocol as used 
by the Google toolbar.  The XML based protocol is documented in 
L{SpellRequest} and L{SpellResult}

@license: GPL
@copyright: 2007 Translate.org.za
@organization: U{Translate.org.za<http://translate.org.za>}, 
    U{WordForge Foundation<http://wordforge.org>}
"""

import httplib
import re
import enchant
import sys
if sys.platform == "win32":
    import win32com.client
    import pythoncom
import os

class SpellChecker:
    """An abstract spell checker class
    """
    def __init__(self, request, pwldir=None):
        """
        @param request: A spell checker request
        @type request: L{SpellRequest}
        @param pwldir: Directory to sore Personal Word Lists
        @type pwldir: string
        """
        self._pwldir = pwldir
        self._request = request

    def check(self):
        """Spell check the text in the supplied request

        @return: The results of the spell check
        @rtype: L{SpellResult}
        """
        pass

    @classmethod
    def langs(cls):
        """Languages available with this spell checker

        @return: Languages that can be spell checked using this spell checker
        @rtype: list of strings
        """
        pass

    def _pwlfilename(self):
        """Creates PWL filename and creates PWL dir if needed

        @return: PWL filename with PWL dir (pwl/dir/enchant-pwl-$lang.dic)
        @rtype: string
        """
        if not os.path.isdir(self._pwldir):
            os.makedirs(self._pwldir)
        filename = self._pwldir + os.sep + "enchant-pwl-" + self._request.lang() + os.extsep + "dic"
        if not os.path.isfile(filename):
            pwlfile = open(filename, "w")
            pwlfile.close()
        return filename

    def _haspwl(self):
        """Is there a PWL available

        @rtype: Boolean
        """
        return not self._pwldir is None

class GoogleChecker(SpellChecker):
    """A spell checker using Google toolbar protocol

    Uses the Google API as used by the Google toolbar which is 
    documented in L{SpellRequest} and L{SpellResult}

    @todo: remove the hardcode pointing to google.com, we should be 
        able to point to servers like our own.
    @todo: we should cache results for words already tested so we 
        can reduce latency but we'd need some way to know what versions 
        we're dealing with.  Might need to distinguish between pure Google
        and an advanced Google-like exchange ie caching Enchant web spellers.
    @bug: this should simply be an enchant provider
    """
    def __init__(self, request, pwldir=None):
        SpellChecker.__init__(self, request, pwldir) 
        if self._haspwl():
            self.__pwldic = enchant.request_pwl_dict(self._pwlfilename())

    def check(self):
        """
        @todo: process using a pwl after its been Google spelled
        """
        connection = httplib.HTTPSConnection("www.google.com")
        try:
            connection.request("POST", 
                "/tbproxy/spell?lang=%s" % self._request.lang(), 
                self._request.request())
            response = connection.getresponse()
            result = SpellResult(self._request, response.read())
            connection.close()
        except Exception, (val, desc):
            if val == 111:
                print "Error (%i): %s" % (val, desc)
                result = SpellResult.error()    
            else:
                raise
        result.parse()
        if self._haspwl():
            wrongwords = self.__pwlcheck(result.spellingMistakes(self._request.text()))
            result.updateErrors(wrongwords)
        return result

    def __pwlcheck(self, words):
        """Find all the incorrectly spelled words by checking against the PWL

        @param words: Words that Google reported as errors
        @type words: list
        @return: words that are still in error according to the PWL
        @rtype: list
        """
        wrongwords = []
        for word in words:
            if not self.__pwldic.check(word):
                wrongwords.append(word)
        return wrongwords

    @classmethod
    def langs(cls):
        return ['da', 'de', 'en', 'es', 'fr', 'it', 'nl', 'pl', 'pt', 'fi', 'sv']

class EnchantChecker(SpellChecker):
    """A spell checker using the enchant spell checker broker

    Enchant acts as a broker to a number of spell checkers including ispell,
    aspell, myspell/hunspell and others.
    """
    def __init__(self,  request, pwldir=None):
        SpellChecker.__init__(self, request, pwldir)
        if not self._haspwl():
            self.__dict = enchant.Dict(self._request.lang())
        else:
            self.__dict = enchant.DictWithPWL(self._request.lang(), self._pwlfilename())

    def check(self):
        result = SpellResult(self._request)
        # FIXME requests should always be in Unicode and we should encode and decode at output
        offset = 0
        text = self._request.texttocheck()

        for word in text.split():
            # Should probably use some kind of proper tokenizer here
            word = re.sub("\*|\&|@|#|-|\+|!|%|\^|\?", "", word)
            if not self.__dict.check(word):
                offset = text.find(word, offset)
                length = len(word)
                suggestions = self.__dict.suggest(word)
                result.add(offset, length, suggestions[0:5])
        return result

    @classmethod
    def langs(cls):
        return enchant.list_languages()

class MSChecker(SpellChecker):
    """A spell checker using Microsoft Office OLE Automation

    @note: This is not a CSAPI spell checker.  Not that we'd mind having one, but
         all the code for doing that is tied up in quite burdensome requirements.  Which 
         essentially mean no FOSS CSAPI.  Apart from of course the reality that you
         can't seem to find anyone at Microsoft to give yuo access to the licence for 
         the CSAPI.  If you are a keen reverse engineering type now is your chance.  Our
         recommendation is that you do two things.  Make a CSAPI spell checker that can
         be used to drive Enchant, thus opening up all OSS spell checkers to users 
         of Microsoft Office.  This is very useful in for instance running Office under WINE
         as then you could use native spell checkers.  Of course you will then have essentially 
         documented the CSAPI interface so that anyone on Windows can use it.  Since its called the
         Common Spell checker API you'd think it was available to all, but actually its only available
         to Office apps.  That is in fact why we have to do OLE here since we cannot access the speller
         DLLs directly. Secondly, give Enchant a CSAPI provider, thus allowing Enchant to 
         call a CSAPI based spell checker.  So running on Windows or in fact even running through
         WINE or similar mechanisms you can use CSAPI based spell checkers.  Useful if you
         want a higher quality checker available through a SpellServer (make sure you 
         have enough licences!).  Google for "SpellerInit CSAPI" to start from almost zero :).
    """

    def __init__(self, request, pwldir=None):
        """
        @param request: A spell checker request
        @type request: L{SpellRequest}
        @param pwldir: Directory to sore Personal Word Lists
        @type pwldir: string

        @note: We probably want to look at a way where we don't create a Microsoft Word 
        instance for each time we check a word.  Rather create something that can be used when the
        server is called or when the checker is first used and that can be reused for each spell check.
        """
        pythoncom.CoInitialize()
        SpellChecker.__init__(self, request, pwldir)
        self.__msword = win32com.client.Dispatch('Word.Application')
        self.__msword.Visible = 0
        self.__worddoc = self.__msword.Documents.Add()

    def __destroy__(self):
        self.__worddoc.Close()
       
    def check(self):
        """
        @note: might be better to check these all at once and not one word at a time.
        """
        result = SpellResult(self._request)
        # FIXME requests should always be in Unicode and we should encode and decode at output
        offset = 0
        text = self._request.texttocheck()

        for word in text.split():
            # Should probably use some kind of proper tokenizer here
            word = re.sub("\*|\&|@|#|-|\+|!|%|\^|\?", "", word)
            if not self.__msword.CheckSpelling(Word=word, CustomDictionary="", 
                      IgnoreUppercase=False, MainDictionary=self._request.lang()):
                offset = text.find(word, offset)
                length = len(word)
                suggestions = self.__msword.GetSpellingSuggestions(Word=word, CustomDictionary="", 
                          IgnoreUppercase=False, MainDictionary="Zulu")
                result.add(offset, length, [unicode(suggestion) for suggestion in suggestions][0:5])
        return result

    @classmethod
    def langs(cls):
        """
        @note: still to determine how to list available languages
        """
        return ['af', 'zu']

class SpellRequest:
    """A spell checker request

    XML Spell Request::
        <?xml version="1.0" encoding="utf-8" ?>
            <spellrequest textalreadyclipped="0" ignoredups="0" ignoredigits="1" ignoreallcaps="1">
                <text>Ths is a tst</text>
            </spellrequest>

    Where the paramaters are:
        - textalreadyclipped - meaning unknown or unused
        - ignoredups - ignore duplicate errors, not exactly sure what this would do
        - ignoredigits - ignore words with any digits in them
        - ignoreallcaps - ignore words in ALL CAPITALS

    In Google the entry in <text> is limited to 20 001 characters.  HTML tags are filtered before testing and 
    are not counted as part of the 20 001.  The tags are simply removed so '... am</p><p>a ...' would be seen
    as the word ama.  So try do your own filtering before submitting to Google.  The spell result offset will
    be with the tags removed.  Simple entities such as &gt;, &lt, &amp; seem to be converted to their actual
    character, while entries such as &copy; result in an error.

    @note: none of these parameters are currently used in the spell checker
    @todo: validate the functioning of some of these options
    @cvar __skeleton: SpellRequest XML skeleton (no pretty printing allowed as Google will 
        then return a failed SpellResult)
    @type __skeleton: string 
    """
    __skeleton = '''<?xml version="1.0" encoding="utf-8" ?><spellrequest textalreadyclipped="0" ignoredups="%i" ignoredigits="%i" ignoreallcaps="%i"><text>%s</text></spellrequest>'''

    def __init__(self, request, lang):
        """
        @param request: XML Spell checker request
        @type request: string
        @param lang: The language to be checked
        @type lang: string

        @todo: can you have more than one <text> request?
        """
        self.__request = request
        self.__lang = lang
        self.__ignoredups = False
        self.__ignoredigits = False
        self.__ignoreallcaps = False
        try:
            options = re.search('<spellrequest textalreadyclipped="(\d)" ignoredups="(\d)" ignoredigits="(\d)" ignoreallcaps="(\d)">', self.__request).groups()
            self.__ignoredups = bool(int(options[1]))
            self.__ignoredigits = bool(int(options[2]))
            self.__ignoreallcaps = bool(int(options[3]))
            self.__text = re.search("<text>(.*?)</text>", self.__request).group(1)
        except AttributeError:
            print "Request XML: '%s'" % self.__request
            raise

    def __str__(self):
        return self.__skeleton % (self.ignoredups(), self.ignoredigits(), self.ignoreallcaps(), self.text())

    def lang(self):
        """Language to check
        
        @return: The language that the user requested to be checked against
        @rtype: string
        """
        return self.__lang

    def request(self):
        """The XML request data

        @return: The raw XML data from the actual request
        @rtype: string
        """
        return self.__request

    def text(self):
        """The raw text supplied for checking

        @rtype: string
        @return: The text supplied for checking
        """
        return self.__text

    def texttocheck(self):
        """The supplied text with non-checking sections removed

        @rtype: string
        @return: The text to be checked

        @bug: doesn't filter correctly to remove ALLCAPS
        """
        tocheck = self.__text
        if self.ignoreallcaps():
            tocheck = re.sub("\b([A-Z]+?)\b", "", tocheck)
        if self.ignoredigits():
            tocheck = re.sub("\b\w*?\d\w*?\b", "", tocheck)
        return tocheck.encode("utf-8")

    def ignoredups(self):
        """Ignore duplicate errors?

        @rtype: boolean
        """
        return self.__ignoredups
    
    def ignoredigits(self):
        """Ignore words with digits?

        @rtype: boolean
        """
        return self.__ignoredigits

    def ignoreallcaps(self):
        """Ignore words in allcaps?

        @rtype: boolean
        """
        return self.__ignoreallcaps

    @classmethod
    def create(cls, text, lang, **kwargs):
        """Create a SpellRequest object
     
        @param text: Text to be spell checked
        @type text: string
        @param lang: Language that you wish to spelling to be conducted in
        @type lang: string
        @param kwargs: (optional) ignoredups, ignoredigits, ignoreallcaps
        @type kwargs: boolean

        @todo: add **kwargs so that we can process options
        """
        request = cls.__skeleton % (
                 kwargs.get("ignoredups") or False, 
                 kwargs.get("ignoredigits") or False, 
                 kwargs.get("ignoreallcaps") or False, 
                 text)
        return SpellRequest(request, lang)

class SpellError:
    """An individual spell checker error

    A L{SpellResult} can contain a number of I{SpellError}s.  These are represented 
    in this class which adds some additional information not present in the raw
    Google XML.

    XML snippet of the Spell Result::
        <c o="0" l="3" s="1">This    Th's        Thus        Th            HS</c>

    Each <c> correction contains a tab delimited list of suggested spellings.  In results from 
    Google the entries are encoded e.g. 't&#xE8;tes' even though the XML header says the data
    is in UTF-8.

    The parameters are:
        - B{o} - the offset
        - B{l} - the length of the misspelled word
        - B{s} - the confidence (not sure how this is used by google) - not used in our results

    See L{SpellResult} for the full represenation of the XML.

    @cvar __skeleton: SpellResult XML skeleton
    @type __skeleton: string 

    """
    __skeleton = '<c o="%d" l="%d" s="%d">%s</c>' 

    def __init__(self, offset, length, suggestions, word=None):
        """
        @param offset: The offset from the start of the text that was checked
        @type offset: Integer
        @param length: The length of the word that was incorrect
        @type length: Integer
        @param suggestions: Spelling suggestions for the misspelled word
        @type suggestions: list
        @param word: The word that was incorrectly spelled
        @type word: String

        """
        self.word = word
        self.offset = offset
        self.length = length
        self.confidence = 1
        self.suggestions = suggestions

    def __str__(self):
        return self.__skeleton % (self.offset, self.length, self.confidence, "\t".join(self.suggestions))
    
class SpellResult:
    """The results from a spell checker request

    This class offers a number of member functions to allow you to construct a result
    from the errors as they are found. Alternatively it can simply act as a holder
    for an existing SpellResult XML snippet which can optionally be parsed.

    XML Spell Result::
        <?xml version="1.0"?>
            <spellresult error="0" clipped="0" charschecked="12" suggestedlang="nl">
                <c o="0" l="3" s="1">This    Th's        Thus        Th            HS</c>
                <c o="9" l="3" s="1">test tat         ST St             st</c>
            </spellresult>

    Attributes:
        - B{error} - Error in the input string.  Occurs if in the <text> request:
                 - you have incomplete HTML tags
                 - you use &copy; type entities
              In this case the other attributes: I{clipped} and I{charschecked} are left out.
        - B{clipped} - Indicates that the supplied text has been clipped.  Is set to "2" when 
              data has been clippped and limits the text to 20 001 characters in charschecked.
        - B{charschecked} - The number of characters checked (limited to 20 001 characters).  
              Will return -1 if there was an error with the input data e.g. malformed SpellRequest.
              It seems that HTML tags are removed from the count of chars checked.
        - B{suggestedlang} - If the test that you are spell checking looks more like another language
              then Google will supply a suggested langauge.  Google toolbar open a dialogue and 
              asks if you would like to change to I{suggestedlang}.


    @cvar __skeleton: SpellResult XML skeleton
    @type __skeleton: string 

    """
    __skeleton = """<?xml version="1.0"?>
    <spellresult error="%i" clipped="%i" charschecked="%i">
        %s
    </spellresults>"""
    __skeleton_no_errors = '<spellresult error="%i" clipped="%i" charschecked="%i"/>'
    def __init__(self, request, rawresult=None):
        """
        @param request: The spelling request to initiated this result
        @type request: L{SpellRequest}
        @param rawresult: An already created XML result packet
        @type rawresult: string
        """
        self.__request = request
        self.__rawresult = rawresult
        self.__needsparsing = not self.__rawresult is None
        self.__errors = {}
        self.__spellheader = {'error': 0, 'clipped': 0}
        
    def __str__(self):
        if self.__rawresult and self.__needsparsing:
            return self.__rawresult
        if len(self.__errors) == 0:
            return self.__skeleton_no_errors % (int(self.__spellheader['error']), int(self.__spellheader['clipped']), self.__getcharschecked())
        else:
            xmlerrors = []
            for error in self.__errors.itervalues():
                xmlerrors.append(str(error))
            return self.__skeleton % (int(self.__spellheader['error']), int(self.__spellheader['clipped']), self.__getcharschecked(), "\n        ".join(xmlerrors))

    def __getcharschecked(self):
        """How many characters where checked.

        @rtype: Integer
        """
        return len(self.__request.text())

    def add(self, offset, length, suggestions, word=None):
        """Add a spelling error and suggestions

        @param offset: The offset of the start of the incorrect word
            from the beginning of the text to be checked.
        @type offset: number
        @param length: The length of the word that is incorrectly spelled.
        @type length: number
        @param suggestions: The list of suggested correct spellings.
        @type suggestions: list of strings
        @param word: The misspelled word as it appears in the text
        @type word: String
        """
        error = SpellError(offset, length, suggestions, word)
        self.__errors[offset] = error

    def updateErrors(self, newerrors):
        """Update the list of errors to only include those in the list provided.

        @param newerrors: a list of error words
        @type newerrors: list 
        """
        updatederrors = {}
        for offset, error in self.__errors.iteritems():
            if error.word in newerrors:
                updatederrors[offset] = error
        self.__errors = updatederrors

    def spellingMistakes(self, originaltext):
        """Extract the spelling errors from the source text

        @param originaltext: The original spelling request
        @type originaltext: string
        @return: a list of words that are incorrectly spelled
        @rtype: list
        """
        errorwords = []
        for error in self.__errors.itervalues():
            errorwords.append(originaltext[error.offset:error.offset+error.length])
        return errorwords

    def parse(self):
        """Parse the object if it was constructed with a raw string
        
        @bug: Google returns suggestions encoded e.g. 't&#xE8;tes', these should really be 
        valid Unicode chars.  We need to convert those back to UTF-8 when parsing.
        @bug: If Google returnd 'suggestedlang' then the regex fails, need to make more 
        robust regex that can handling any new options, probably placing them in a dict.
        """
        if not (self.__rawresult and self.__needsparsing):
            return
        spellintro = re.search('(<spellresult [^>]*>)', self.__rawresult).groups()[0]
        for attribute, value in re.findall('([^= ]+)="([^"]+)"[^\S]*', spellintro):
            self.__spellheader[attribute] = value
        for suggestion in re.findall('(<c o="\d+?" l="\d+?" s="\d+?">.+?</c>)', self.__rawresult):
            offset, length, quality, suggestions = re.search('<c o="(\d+?)" l="(\d+?)" s="(\d+?)">(.+?)</c>', suggestion).groups()
            offset, length, quality = int(offset), int(length), int(quality)
            self.add(offset, length, suggestions.split("\t"), self.__request.text()[offset:offset+length])
        self.__needsparsing = False

    @classmethod
    def parseString(cls, spellresult):
        """Create a SpellResult from an XML string

        @param spellresult: XML SpellResult
        @type spellresult: string
        @rtype: SpellResult
        """
        result = SpellResult(rawresult=spellresult)
        result.parse()
        return result

    @classmethod
    def error(cls):
        """Create an error result
       
        @rtype: string
        """
        print "Our error"
        return '''<?xml version="1.0"?>
<spellresult error="0" clipped="0" charschecked="-1"/>'''
