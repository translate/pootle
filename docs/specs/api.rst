Pootle API
~~~~~~~~~~

Motivation
==========
#. Mozilla wants to be able to get status and contribution information from
   Pootle; what needs to be done, what has someone contributed.
#. We want Solas to be able to interact with Pootle and initiate and publish
   translatable jobs to Pootle so that it can provide a web based translation
   environment to Solas translation projects.
#. Users and system administrations want to be able to interact with Pootle
   without needing shell access.

Use Cases
=========
* Barry has a project hosted on pootle.locamotion.org and wants to automate
  pushing and updating strings.  At the moment he can't since he has no command
  line access but with an API and CLI tool he can automate this in bash scripts
  or in other programming languages.

**Mozilla related**

* Mozilla wants to be able to retrieve the contributions from a given
  translator to display them in its telephone directory.
* Mozilla wants to be able to report work that still needs to be done.

**Solas related**

* Solas has a new project that it wants to initiate on Pootle.  When initiating
  it wants to supply the languages, files, descriptions and translators
  assigned to the project.
* Solas wants to update descriptions to match those in the project.
* Solas wants to update files following a fresh of the source document.
* Solas wants an idea of the progress being made on Pootle to report to its
  users.
* When a project is complete Solas wants to remove it from Pootle.

Implementation
==============

Abilities required
------------------

**Project related**

Projects should be defined in a .ttk folder or in the api

* init (create) -- create a project [#solas]_ [#saas]_
* rm (delete) - remove a project [#solas]_
* add -- add language(s) to a project [#solas]_  [#saas]_
* drop -- drop language(s) from a project [#solas]_  [#saas]_
* assign - assign a translator to a language with certain rights [#solas]_  [#saas]_
* remove - remove a translator from a project [#solas]_  [#saas]_
* describe - change meta data for a project [#solas]_  [#saas]_
* statistics -- get statistics for a project: languages, avg completion, etc. [#moz]_ [#solas]_  [#saas]_

.. Should we call get and put, push and pull to match DVCS semantics?

* get (pull) -- retrieve translations from Pootle [#solas]_ [#saas]_
* put (push) -- publish translations to Pootle [#solas]_ [#saas]_
* list -- list languages [#solas]_ [#saas]_

**User related**

* create - create a new user [#solas]_
* password - change/set the password [#solas]_
* delete -- delete a user from the server (must think about how we keep historic
  data) [#solas]_
* statistics - data for that user within given dates: projects, translations,
  suggestions, etc [#moz]_ [#solas]_

**File related**

* list - list of available files [#virtaal]_
* statistics - stats at a file level [#virtaal]_

**Unit related**

.. The names don't feel right

* list_units - get a list of units that match a criterion [#virtaal]_
* get_unit - retrieve a unit for translation [#virtaal]_

.. The following two could be the same just different modes or rights.

* translate - provide a translation for a unit [#virtaal]_
* suggest - provide a suggestion for a unit [#virtaal]_

.. rubric:: Command footnotes

.. [#moz] Needed by Mozilla
.. [#solas] Needed for Solas integration
.. [#virtaal] Using Virtaal to translate offline
.. [#saas] Delivering Pootle as a service


Django side
-----------
We'll use `tastypie <http://tastypieapi.org/>`_ to handle the RESTful API.

- Authentication -- need to check how we would do this.

Zero stage
----------
Initial tastypie implementation that puts in all the infrastructure for the
API. Including updates to ``requirements/``, documentation, etc.

API version will be ``0.9`` until stabilised.

Basic API implementation for list_languages and a command line tool that could
call it.

First stage
-----------
Provide stats for Mozilla in terms of translations contributed. Provide a
linkable badge for users to brag about translations that makes use of this API.

Second stage
------------
We'll address the command line approach as a test implementation.  Thus
allowing all actions from a ``pootle-cli`` tool.  This will allow us to iron
out issues and easily test error reporting and failures. When it passes that
would mean that we can safely expose this to external tools.

Third stage
--------------
Actual Pootle <--> Solas interaction.  So expose the API and give feedback to
the team on collaboration.

Fourth stage
---------------
Using Virtaal. Some ideas:

* Ability to list public Pootle servers
* Ability to drill into projects
* Request a language
* See list of files and completion like a catalog manager
* Perform translations

API stability
=============
* There are no plans for a stable API until v1.0
* Once we declare v1.0 we'll keep a stable API for that until deprecated by v2.0
