# Build our database and ORM stuff.  Documentation is available at
# http://www.sqlalchemy.org/docs/05/ormtutorial.html#datamapping_tables

from sqlalchemy import *
from sqlalchemy.orm import *

metadata = MetaData()

# Alchemy Table Definitions
languages = Table('languages', metadata,
  Column('id', Integer, primary_key=True), 
  Column('code', String(50), nullable=False, unique=True), 
  Column('fullname', Unicode(255), nullable=False), 
  Column('nplurals', Integer), 
  Column('pluralequation', String(255)), 
  Column('specialchars', Unicode(255), server_default=""), 
  mysql_engine='innodb',
  mysql_charset='utf8'
)

_projects  = Table('projects', metadata,
  Column('id', Integer, primary_key=True),
  Column('code', Unicode(255), nullable=False, unique=True),
  Column('fullname', Unicode(255), nullable=False),
  Column('description', Text),
  Column('checkstyle', String(50), nullable=False),
  Column('localfiletype', String(50), server_default=""),
  Column('createmofiles', Boolean, server_default="0"),
  Column('treestyle', String(20), server_default=""),
  Column('ignoredfiles', Unicode(255), nullable=False, server_default=""),
  mysql_engine='innodb',
  mysql_charset='utf8'
)

submissions  = Table('submissions', metadata,
  Column('id', Integer, primary_key=True),
  Column('creationTime', DateTime),
  Column('languageID', Integer, ForeignKey('languages.id')),
  Column('projectID', Integer, ForeignKey('projects.id')),
  Column('filename', Unicode(255)),
  Column('source', Unicode(255)),
  Column('trans', Unicode(255)),
  Column('submitterID', Integer, ForeignKey('users.id')),
  mysql_engine='innodb',
  mysql_charset='utf8'
)

suggestions  = Table('suggestions', metadata,
  Column('id', Integer, primary_key=True),
  Column('creationTime', DateTime),
  Column('languageID', Integer, ForeignKey('languages.id')),
  Column('projectID', Integer, ForeignKey('projects.id')),
  Column('filename', Unicode(255)),
  Column('source', UnicodeText),
  Column('trans', UnicodeText),
  Column('suggesterID', Integer, ForeignKey('users.id')),
  Column('reviewerID', Integer, ForeignKey('users.id')),
  Column('reviewStatus', String(30), server_default="pending"),
  Column('reviewTime', DateTime),
  Column('reviewSubmissionID', Integer, ForeignKey('submissions.id')),
  mysql_engine='innodb',
  mysql_charset='utf8'
)

user_languages = Table('user_languages', metadata,
  Column('user_id', Integer, ForeignKey('users.id')),
  Column('language_id', Integer, ForeignKey('languages.id')),
  mysql_engine='innodb',
  mysql_charset='utf8'
)

user_projects = Table('user_projects', metadata,
  Column('user_id', Integer, ForeignKey('users.id')),
  Column('project_id', Integer, ForeignKey('projects.id')),
  mysql_engine='innodb',
  mysql_charset='utf8'
)

users = Table('users', metadata,
  Column('id', Integer, primary_key=True, autoincrement=True), 
  Column('username', Unicode(255), nullable=False, index=True, unique=True), 
  Column('name', Unicode(255), nullable=False, server_default=""), 
  Column('email', Unicode(255), nullable=False, server_default=""), 
  Column('activated', Boolean, nullable=False, server_default="0"), 
  Column('activationcode', String(255)), 
  Column('passwdhash', String(255)), 
  Column('logintype', String(20)), 
  Column('siteadmin', Boolean, nullable=False, server_default="0"), 
  Column('viewrows', Integer, nullable=False, server_default="10"), 
  Column('translaterows', Integer, nullable=False, server_default="10"),
  Column('uilanguage', String(50), ForeignKey('languages.code')), 
  Column('altsrclanguage', String(50), ForeignKey('languages.code')), 
  mysql_engine='innodb',
  mysql_charset='utf8'
)

# Create classes for our tables
class Project(object):
  def __init__(self, code, fullname = u"", description = "", checkstyle = "", localfiletype = "", createmofiles=False, treestyle="", ignoredfiles=u""):
    self.code = code
    self.fullname = fullname 
    self.description = description 
    self.checkstyle = checkstyle 
    self.localfiletype = localfiletype 
    self.createmofiles = createmofiles
    self.treestyle = treestyle
    self.ignoredfiles = ignoredfiles

  def __repr__(self):
    return "<Project %s: %s>" % (self.code, self.fullname.encode('utf8'))

class Language(object):
  def __init__(self, code, fullname = u"", nplurals = 1, pluralequation = "", specialchars=u""):
    self.code = code
    self.fullname = fullname 
    self.nplurals = nplurals 
    self.pluralequation = pluralequation 
    self.specialchars = specialchars

  def __repr__(self):
    return "<Language %s: %s>" % (self.code, self.fullname.encode('utf8'))

class Submission(object):
  pass

class Suggestion(object):
  pass

class User(object):

  def __init__(self, username=u''):
    self.username = username 
    self.name = u''
    self.email = u''
    self.activated = False
    self.activationcode = None
    self.passwdhash = None
    self.logintype = None
    self.siteadmin = False 
    self.viewrows = 10
    self.translaterows = 10
    self.uilanguage = 'en'
    self.altsrclanguage = 'en'

  def __repr__(self):
    return "<User %s (%s) <%s>>" % (self.username.encode('utf8'), self.name.encode('utf8'), self.email.encode('utf8'))

  def suggestionsMadeCount(self):
    return len(self.suggestionsMade)

  def suggestionsAcceptedCount(self):
    return len(self.suggestionsAccepted)

  def suggestionsPendingCount(self):
    return len(self.suggestionsPending)

  def suggestionsRejectedCount(self):
    return len(self.suggestionsRejected)

  def suggestionsReviewedCount(self):
    return len(self.suggestionsReviewed)

  def submissionsCount(self):
    return len(self.submissions)

  def suggestionUsePercentage(self):
    accepted = self.suggestionsAcceptedCount()
    rejected = self.suggestionsRejectedCount()
    beenreviewed = accepted+rejected
    if beenreviewed == 0:
      return 0
    return 100 * accepted / beenreviewed 

 
# Create a mapping between class and table and build ORM relationships.  Note the backreferences.
mapper(Language, languages)
mapper(Project, _projects)
mapper(Submission, submissions, properties={
    'language'  : relation(Language, backref='submissions'),
    'project'   : relation(Project, backref='submissions'),
    'submitter' : relation(User, backref='submissions')
  })
mapper(Suggestion, suggestions, properties={
    'suggester'        : relation(User, primaryjoin=suggestions.c.suggesterID==users.c.id, backref='suggestionsMade'),
    'reviewer'         : relation(User, primaryjoin=suggestions.c.reviewerID==users.c.id, backref='suggestionsReviewed'),
    'language'         : relation(Language, backref='suggestions'),
    'project'          : relation(Project, backref='suggestions'),
    'reviewSubmission' : relation(Submission, backref=backref('fromsuggestion', uselist=False))
  })
mapper(User, users, properties={
    'projects'            : relation(Project, secondary=user_projects, backref='users'),
    'languages'           : relation(Language, secondary=user_languages, backref='users'),
    'uilanguageobj'       : relation(Language, primaryjoin=users.c.uilanguage==languages.c.code, backref='uiusers'),
    'altsrclanguageobj'   : relation(Language, primaryjoin=users.c.altsrclanguage==languages.c.code, backref='altsrcusers'),
    'suggestionsAccepted' : relation(Suggestion, primaryjoin=and_(suggestions.c.suggesterID==users.c.id, suggestions.c.reviewStatus=="accepted")),
    'suggestionsRejected' : relation(Suggestion, primaryjoin=and_(suggestions.c.suggesterID==users.c.id, suggestions.c.reviewStatus=="rejected")),
    'suggestionsPending'  : relation(Suggestion, primaryjoin=and_(suggestions.c.suggesterID==users.c.id, suggestions.c.reviewStatus=="pending"))
  })
