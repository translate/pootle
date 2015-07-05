# Python 3 compatibility
try:
    unicode
except NameError:
    unicode = str


class autoencode(unicode):
    """
    Supports a hybrid Unicode string that knows which encoding is preferable,
    and uses this when converting to a string.
    """

    def __new__(newtype, string=u"", encoding=None, errors=None):
        if isinstance(string, unicode):
            if errors is None:
                newstring = unicode.__new__(newtype, string)
            else:
                newstring = unicode.__new__(newtype, string, errors=errors)
            if encoding is None and isinstance(string, autoencode):
                newstring.encoding = string.encoding
            else:
                newstring.encoding = encoding
        else:
            if errors is None and encoding is None:
                newstring = unicode.__new__(newtype, string)
            elif errors is None:
                try:
                    newstring = unicode.__new__(newtype, string, encoding)
                except LookupError as e:
                    raise ValueError(str(e))
            elif encoding is None:
                newstring = unicode.__new__(newtype, string, errors)
            else:
                newstring = unicode.__new__(newtype, string, encoding, errors)
            newstring.encoding = encoding
        return newstring

    def __str__(self):
        if self.encoding is None:
            return super(autoencode, self).__str__()
        else:
            return self.encode(self.encoding)

    def join(self, seq):
        return autoencode(super(autoencode, self).join(seq))


class multistring(autoencode):
    """
    Supports a hybrid Unicode string that can also have a list of alternate
    strings in the strings attribute
    """
    def __new__(newtype, string=u"", encoding=None, errors=None):
        if isinstance(string, list):
            if not string:
                raise ValueError("multistring must contain at least one string")
            mainstring = string[0]
            newstring = multistring.__new__(newtype, string[0],
                                            encoding, errors)
            newstring.strings = [newstring] + [
                autoencode.__new__(autoencode, altstring, encoding, errors) for altstring in string[1:]
            ]
        else:
            newstring = autoencode.__new__(newtype, string, encoding, errors)
            newstring.strings = [newstring]
        return newstring

    def __init__(self, *args, **kwargs):
        super(multistring, self).__init__()
        if not hasattr(self, "strings"):
            self.strings = []

    def __cmp__(self, otherstring):
        if isinstance(otherstring, multistring):
            parentcompare = cmp(autoencode(self), otherstring)
            if parentcompare:
                return parentcompare
            else:
                return cmp(self.strings[1:], otherstring.strings[1:])
        elif isinstance(otherstring, autoencode):
            return cmp(autoencode(self), otherstring)
        elif isinstance(otherstring, unicode):
            return cmp(unicode(self), otherstring)
        elif isinstance(otherstring, str):
            return cmp(str(self), otherstring)
        elif isinstance(otherstring, list) and otherstring:
            return cmp(self, multistring(otherstring))
        else:
            return cmp(type(self), type(otherstring))

    def __ne__(self, otherstring):
        return self.__cmp__(otherstring) != 0

    def __eq__(self, otherstring):
        return self.__cmp__(otherstring) == 0

    def __repr__(self):
        parts = [autoencode.__repr__(self)] + [repr(a) for a in self.strings[1:]]
        return "multistring([%s])" % (",".join(parts))

    def replace(self, old, new, count=None):
        if count is None:
            newstr = multistring(super(multistring, self) \
                   .replace(old, new), self.encoding)
        else:
            newstr = multistring(super(multistring, self) \
                   .replace(old, new, count), self.encoding)
        for s in self.strings[1:]:
            if count is None:
                newstr.strings.append(s.replace(old, new))
            else:
                newstr.strings.append(s.replace(old, new, count))
        return newstr
