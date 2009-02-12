# mozldap.py
# An implementation of Mozilla LDAP user lookup in python.  Originally based on:
# http://svn.mozilla.org/addons/trunk/site/app/controllers/components/ldap.php
# (revision 15278)

# Author: Dan Schafer <dschafer@mozilla.com>
# Date: 10 Jun 2008

# Requires python-ldap module from http://python-ldap.sourceforge.net/
import ldap

class MozillaLdap:
  """ LDAP class for connecting to mozilla's LDAP server
  
  An instance of this class must be given a host, an anonymous user name and 
  an anonymous password.  It is guaranteed that at the start and end of any
  public method, an instance of this class will be bound to the LDAP server.
 
  The public methods are designed to be fairly general: if this class is to
  be used on a different LDAP system, only the private methods should need
  to be changed.

  Any exception defined in LDAP might be raised by a method at appropriate
  times.  Additionally, any method that expects an entry to exist in the
  LDAP will raise NoSuchAccount if it does not find such an entry.  Finally,
  if a method requires that it identify a unique LDAP entry, but more than one
  is found by the LDAP search, AmbiguousAccount will be raised.

  """

  def __init__(self, host, anon, anonpass):
    """Creates the connvection to the server, and binds anonymously"""
    self.LDAP_HOST = host
    self.ANON_BIND = anon
    self.ANON_BIND_PW = anonpass

    # Initialize the LDAP object
    self.ldo = ldap.initialize(self.LDAP_HOST)
    self.__bindAnon()

  def __bindAnon(self):
    """Bind to the server using the anonymous credentials"""

    self.ldo.simple_bind_s(self.ANON_BIND, self.ANON_BIND_PW)

  def __mailsearch(self, email):
    """Do a search on the given e-mail address; returns the standard
    result of search_s query.
    
    """

    return self.ldo.search_s("dc=mozilla", ldap.SCOPE_SUBTREE, "mail="+email)

  def __usernamesearch(self, username):
    """Do a search on the given username; returns the standard
    result of search_s query.  In this implementation, we just
    call __mailsearch, since Mozilla just uses e-mail addresses
    as usernames; however, this is the only function in which
    that assumption is made, so it is easily adaptable to a
    non-email based username system.
    
    """

    return self.__mailsearch(username)

  def __hasRights(self, acctDict, acctType):
    """Tests to see if the user with LDAP returned dictionary acctDict has
    the rights specified by acctType; this is a separate method because it
    is LDAP implementation specific.
  
    """

    return (acctType in acctDict['objectClass'])

  def __findFullName(self, acctDict):
    """Returns the full name from the provided LDAP entry"""

    return "%s %s" % (acctDict['givenName'][0], acctDict['sn'][0])


  def __getDn(self, username):
    """Private method to find the distinguished name for a given username"""

    sres = self.__usernamesearch(username)
    if len(sres) > 1:
      raise AmbiguousAccount(email, len(sres))
    if len(sres) == 0:
      raise NoSuchAccount(username)
    
    # sres[0][0] is the distinguished name of the first result
    return sres[0][0]

  def connect(self, username, password):
    """ Retrieves the distinguished name associated with the given username,
    then binds to the server using that distinguished name and the given
    password.

    If the bind fails, the appropriate exception will be raised after the
    connection is rebound using the anonymous credentials, as per the
    invariant described in the class docstring that this object must be
    bound to the server after any public method exits.

    """
    
    # No try/except around getDn: anything it raises we want to pass on
    dn = self.__getDn(username)

    try:
      self.ldo.simple_bind_s(dn, password)
    except:
      # If the bind failed, that's fine, but ldo needs to be bound
      # to preserve our invariant
      self.__bindAnon()
      raise

  def isCorrectCredentials(self, username, password):
    """Tries to connect to the server using the given username and password,
    and returns whether the connection was successful, which also indicates
    whether the given username and password were valid credentials.

    """

    try: # Let's see if connecting works! 
      self.connect(username, password)
    except NoSuchAccount: # Bad e-mail, credentials are bad.
      return False
    except ldap.INVALID_CREDENTIALS: # Bad password, credentials are bad.
      return False
    except ldap.UNWILLING_TO_PERFORM: # Bad password, credentials are bad.
      return False
    except: # No other exceptions are normal, so we raise this.
      raise
    else: # No exceptions: the connection succeeded and the user exists!
      return True

  def hasAccountType(self, email, acctType):
    """Finds the entry in the LDAP with the desired e-mail address, then
    determines (using __hasRights) whether that entry is of type acctType.

    """
   
    sres = self.__mailsearch(email)
    
    if len(sres) > 1:
      raise AmbiguousAccount(email, len(sres))
    if len(sres) == 0:
      raise NoSuchAccount(email)
    acctDict = sres[0][1]
    return self.__hasRights(acctDict, acctType) 

  def getFullName(self, email):
    """Returns the full name of the perswon with the given e-mail, or throws
    an appropriate exception (NoSuchAccount or AmbiguousAccount)

    """

    sres = self.__mailsearch(email)
    if len(sres) > 1:
      raise AmbiguousAccount(email, len(sres))
    if len(sres) == 0:
      raise NoSuchAccount(email)
    acctDict = sres[0][1]
    return self.__findFullName(acctDict)


  def hasAccount(self, email):
    """Given an e-mail, returns a boolean indicating if there is a valid LDAP
    entry with that e-mail.

    """
    
    sres = self.__mailsearch(email)
      
    if len(sres) > 1:
      raise AmbiguousAccount(email, len(sres))
    if len(sres) == 1:
      return True
    return False # Length must have been 0; no account exists

class AmbiguousAccount(Exception):
  """Exception thrown when an LDAP operation returned too many users.""" 

  def __init__(self, username, numusers):
    self.username = username
    self.numusers = numusers
  def __str__(self):
    return "Ambiguous Account: %d users found for username %s." \
    % (self.numusers, self.username)

class NoSuchAccount(Exception):
  """Exception thrown when an operation returned no users, and users were
  expected.
  
  """

  def __init__(self, username):
    self.username = username
  def __str__(self):
    return "No Such Account: username %s." \
    % (self.username)
