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
* Solas wants to update descriptions on Pootle to match those in the upstream
  project.
* Solas wants to update files following a refresh of the source document.
* Solas wants an information about the progress being made on Pootle to report
  to its users.
* When a project is complete Solas wants to remove it from Pootle.

Implementation
==============

Projects should be defined in a ``.pootle`` configuration folder for the
command line tool or in the API.

Abilities required
------------------

* ``<LANG>`` is the language PK (not the code)
* ``<USER>`` is the user PK (not the username)
* ``<PROJ>`` is the project PK (not the code)
* ``<TRAP>`` is the translation project PK
* ``<STOR>`` is the store PK
* ``<UNIT>`` is the unit PK
* ``<SUGG>`` is the suggestion PK


.. warning::
   * **Q:** I think it would make sense to allow codes to be used.
   * **A:** Tried but was problematic. Perhaps I was told to change how the
     resource URI is generated.

     **TODO**: I need to check
     http://django-tastypie.readthedocs.org/en/latest/resources.html#get-resource-uri
     but this will be left for the future.


.. warning:: **TODO**: Need to look at caching. But this will be left for the
   future.


.. note::
   * **Q:** Review all command names because might be inconsistent. Also need to
     talk about the commands, because this is not an API thing but something
     used in ``pootle-cli`` perhaps.
   * **A:** Makes sense to split off the CLI implementation beyond a basic tool
     for now.  The tool will have a very different interaction with the server I
     think.  I think we should at least align the command names. E.g. to create
     a new <LANG> we had *add*, while a <USER> we have *create*.


.. warning::
   * **Q:** Need to make clear at which levels translations can be pushed or
     retrieved. I assume that the original idea was to push files.

     Perhaps we should start with a low level API and then add that ability at
     upper levels. By that I mean pushing single units and then add the ability
     for sending/retrieving files (stores), and after that perhaps add at upper
     levels (TP, project or subsets of those two).

   * **A:** Yes, the original idea in ttk-get and ttk-put is to push and pull
     files.  Also for Solas it would be that ability. 

     I'm not sure what the lowest level should be, I guess unit for live
     interaction e.g. Virtaal translating live against Pootle DB. Or a live
     website wanting to see flow of translations.

     But for most project related I would see this as a store, while a store is
     a collection of units it is what Pootle is using. Unit level allows clearer
     abstraction of searching and checks I would guess.

     Some **discussion needed here** I think.


.. note:: **DB**: Should we call get and put, push and pull to match DVCS
   semantics?  I'm leaning to pull and push.

* get (pull) -- retrieve translations from Pootle [#solas]_ [#saas]_
* put (push) -- publish translations to Pootle [#solas]_ [#saas]_


Language related
^^^^^^^^^^^^^^^^

+----------+----------------+--------+----------------------------------+------------+
| Command  | Description    | Method | URL                              | Needed for |
+==========+================+========+==================================+============+
| list     | List all       | GET    | ``/languages/``                  |            |
|          | languages      |        |                                  |            |
+----------+----------------+--------+----------------------------------+------------+
| create   | Create a       | POST   | ``/languages/``                  |            |
|          | language       |        |                                  |            |
+----------+----------------+--------+----------------------------------+------------+
| show     | Get the data   | GET    | ``/languages/<LANG>/``           |            |
|          | for a language |        |                                  |            |
|          | (including its |        |                                  |            |
|          | projects)      |        |                                  |            |
+----------+----------------+--------+----------------------------------+------------+
| change   | Change the data| PATCH  | ``/languages/<LANG>/``           |            |
|          | for a language | or PUT |                                  |            |
+----------+----------------+--------+----------------------------------+------------+
| delete   | Remove a       | DELETE | ``/languages/<LANG>/``           |            |
|          | language       |        |                                  |            |
+----------+----------------+--------+----------------------------------+------------+
| stats    | Get statistics | GET    | ``/languages/<LANG>/statistics/``|            |
|          | for a language |        |                                  |            |
+----------+----------------+--------+----------------------------------+------------+


User related
^^^^^^^^^^^^

+----------+----------------+--------+------------------------------+------------+
| Command  | Description    | Method | URL                          | Needed for |
+==========+================+========+==============================+============+
| create   | Create a new   | POST   | ``/users/``                  | [#solas]_  |
|          | user           |        |                              |            |
+----------+----------------+--------+------------------------------+------------+
| show     | Show the data  | GET    | ``/users/<USER>/``           |            |
|          | for a user     |        |                              |            |
+----------+----------------+--------+------------------------------+------------+
| change   | Change the data| PATCH  | ``/users/<USER>/``           |            |
|          | for a user     | or PUT |                              |            |
+----------+----------------+--------+------------------------------+------------+
| password | Change/set the | PATCH  | ``/users/<USER>/``           | [#solas]_  |
|          | password       | or PUT |                              |            |
+----------+----------------+--------+------------------------------+------------+
| delete   | Delete a user  | DELETE | ``/users/<USER>/``           | [#solas]_  |
|          | from the server|        |                              |            |
|          | (is_active will|        |                              |            |
|          | be set to      |        |                              |            |
|          | False)         |        |                              |            |
+----------+----------------+--------+------------------------------+------------+
| stats    | Data for that  | GET    | ``/users/<USER>/statistics/``| [#moz]_    |
|          | user within    |        |                              | [#solas]_  |
|          | given dates:   |        |                              |            |
|          | projects,      |        |                              |            |
|          | translations,  |        |                              |            |
|          | suggestions,   |        |                              |            |
|          | etc.           |        |                              |            |
+----------+----------------+--------+------------------------------+------------+


.. note:: Users won't be listed for security reasons.


.. warning:: **TODO**: Still need to define if PootleProfile, or User, or a
   mixture is exposed.


Project related
^^^^^^^^^^^^^^^

+----------+----------------+--------+----------------------------------+------------+
| Command  | Description    | Method | URL                              | Needed for |
+==========+================+========+==================================+============+
| list     | List all       | GET    | ``/projects/``                   |            |
|          | projects       |        |                                  |            |
+----------+----------------+--------+----------------------------------+------------+
| init     | Create a       | POST   | ``/projects/``                   | [#solas]_  |
|          | project        |        |                                  | [#saas]_   |
+----------+----------------+--------+----------------------------------+------------+
| show     | Get a project  | GET    | ``/projects/<PROJ>/``            |            |
|          | data or        |        |                                  |            |
|          | description    |        |                                  |            |
+----------+----------------+--------+----------------------------------+------------+
| describe | Change data    | PATCH  | ``/projects/<PROJ>/``            | [#solas]_  |
|          | for a project  | or PUT |                                  | [#saas]_   |
+----------+----------------+--------+----------------------------------+------------+
| rm       | Remove a       | DELETE | ``/projects/<PROJ>/``            | [#solas]_  |
|          | project        |        |                                  |            |
+----------+----------------+--------+----------------------------------+------------+
| stats    | Get statistics | GET    | ``/projects/<PROJ>/statistics/`` | [#moz]_    |
|          | for a project: |        |                                  | [#solas]_  |
|          | languages, avg |        |                                  | [#saas]_   |
|          | completion,    |        |                                  |            |
|          | etc.           |        |                                  |            |
+----------+----------------+--------+----------------------------------+------------+


Translation project (language in project) related
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+----------+--------------------+--------+----------------------------------------------+------------+
| Command  | Description        | Method | URL                                          | Needed for |
+==========+====================+========+==============================================+============+
| langs    | List languages     | GET    | ``/projects/<PROJ>/``                        | [#solas]_  |
|          | (translation       |        |                                              | [#saas]_   |
|          | projects) in a     |        |                                              |            |
|          | project            |        |                                              |            |
+----------+--------------------+--------+----------------------------------------------+------------+
| projs    | List projects      | GET    | ``/languages/<LANG>/``                       |            |
|          | (translation       |        |                                              |            |
|          | projects) in a     |        |                                              |            |
|          | language           |        |                                              |            |
+----------+--------------------+--------+----------------------------------------------+------------+
| add      | Add a translation  | POST   | ``/translation-projects/``                   | [#solas]_  |
|          | project (add a     |        |                                              | [#saas]_   |
|          | language to a      |        |                                              |            |
|          | project, or a      |        |                                              |            |
|          | project to a       |        |                                              |            |
|          | language)          |        |                                              |            |
+----------+--------------------+--------+----------------------------------------------+------------+
| show     | Show translation   | GET    | ``/translation-projects/<TRAP>/``            |            |
|          | project data       |        |                                              |            |
+----------+--------------------+--------+----------------------------------------------+------------+
| change   | Change translation | PATCH  | ``/translation-projects/<TRAP>/``            |            |
|          | project data       | or PUT |                                              |            |
+----------+--------------------+--------+----------------------------------------------+------------+
| drop     | Drop translation   | DELETE | ``/translation-projects/<TRAP>/``            | [#solas]_  |
|          | project (from a    |        |                                              | [#saas]_   |
|          | project and a      |        |                                              |            |
|          | language)          |        |                                              |            |
+----------+--------------------+--------+----------------------------------------------+------------+
| stats    | Get statistics for | GET    | ``/translation-projects/<TRAP>/statistics/`` |            |
|          | a translation      |        |                                              |            |
|          | project            |        |                                              |            |
+----------+--------------------+--------+----------------------------------------------+------------+


Permissions in translation project related
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+----------+--------------------+--------+--------------------------------------------------+------------+
| Command  | Description        | Method | URL                                              | Needed for |
+==========+====================+========+==================================================+============+
| listtrans| List translators   | GET    | ``/translation-projects/<TRAP>/users/``          |            |
|          | in a translation   |        |                                                  |            |
|          | project            |        |                                                  |            |
+----------+--------------------+--------+--------------------------------------------------+------------+
| assign   | Assign a           | POST   | ``/translation-projects/<TRAP>/users/``          | [#solas]_  |
|          | translator to      |        |                                                  | [#saas]_   |
|          | a language         |        |                                                  |            |
|          | with certain       |        |                                                  |            |
|          | rights             |        |                                                  |            |
+----------+--------------------+--------+--------------------------------------------------+------------+
| ls_perm  | Show permissions   | GET    | ``/translation-projects/<TRAP>/users/<USER>/``   | [#solas]_  |
|          | for a translator   |        |                                                  | [#saas]_   |
|          | in a project       |        |                                                  |            |
+----------+--------------------+--------+--------------------------------------------------+------------+
| ch_perm  | Change permissions | PATCH  | ``/translation-projects/<TRAP>/users/<USER>/``   |            |
|          | for a translator   | or PUT |                                                  |            |
|          | in a project       |        |                                                  |            |
+----------+--------------------+--------+--------------------------------------------------+------------+
| remove   | Remove a translator| DELETE | ``/translation-projects/<TRAP>/users/<USER>/``   | [#solas]_  |
|          | from a language    |        |                                                  | [#saas]_   |
+----------+--------------------+--------+--------------------------------------------------+------------+


.. warning::
   * **Q:** Make clear if users are assigned/removed to a "translation project"
     and/or in other levels (languages or projects or stores).
   * **A:** We have this problem in Pootle.  Do you have rights because you are
     site admin, manage a project, manage a language or given rights in this TP.

   **TODO**: This could need more discussion.


File (store) related
^^^^^^^^^^^^^^^^^^^^

+----------+---------------+--------+-----------------------------------+------------+
| Command  | Description   | Method | URL                               | Needed for |
+==========+===============+========+===================================+============+
| list     | List of       | GET    | ``/translation-projects/<TRAP>/`` | [#virtaal]_|
|          | available     |        |                                   |            |
|          | files in a    |        |                                   |            |
|          | translation   |        |                                   |            |
|          | project       |        |                                   |            |
+----------+---------------+--------+-----------------------------------+------------+
| filter   | List stores by| GET    | ``/stores/``                      |            |
|          | using a given |        |                                   |            |
|          | filter(s)     |        |                                   |            |
+----------+---------------+--------+-----------------------------------+------------+
| show     | Show the data | GET    | ``/stores/<STOR>/``               |            |
|          | for the store |        |                                   |            |
+----------+---------------+--------+-----------------------------------+------------+
| get      | Download the  | GET    | ``/stores/<STOR>/file/``          | [#virtaal]_|
|          | translation   |        |                                   |            |
|          | file for the  |        |                                   |            |
|          | store         |        |                                   |            |
+----------+---------------+--------+-----------------------------------+------------+
| put      | Upload a      | PUT    | ``/stores/<STOR>/file/``          | [#virtaal]_|
|          | translation   |        |                                   |            |
|          | file for the  |        |                                   |            |
|          | store         |        |                                   |            |
+----------+---------------+--------+-----------------------------------+------------+
| stats    | Statistics for| GET    | ``/stores/<STOR>/statistics/``    | [#virtaal]_|
|          | a given file  |        |                                   |            |
+----------+---------------+--------+-----------------------------------+------------+
| checks   | Shows the     | GET    | ``/stores/<STOR>/checks/``        |            |
|          | failing checks|        |                                   |            |
|          | for a file    |        |                                   |            |
+----------+---------------+--------+-----------------------------------+------------+


.. note::
   * **Q:** Are we going to allow deleting/adding/changing Files using the API?
   * **A:** Upload/download files yes. Deleting files not, at least for now.
     Stores won't be added/deleted/changed.


.. warning::
   * **Q:** Need to define which filters could be used.

     Dwayne Bailey said (in previous chat):
   
     * In Pootle we have directories which also help filter which stores we're
       talking about.
     * We also filter and are able to find units matching some criterion.
     * So being able to know about the directory layout would be one issue, I
       guess it could be part of the store data.
     * And then being able to find units from a certain level or matching some
       criterion.

     **NOTE:** The store saves the ``pootle_path`` and ``parent`` directory. So
     perhaps
     http://django-tastypie.readthedocs.org/en/latest/resources.html#basic-filtering
     could be useful. Need to make checks first in Units.


   * **A:** The directory structure is just a special way of grouping
     stores. So if the store know it's paths and parents if would be quite easy.
     And if we are maybe able to filter and say show me all stores at this
     level.

     The one issue would be directories, that is how do we show that at this
     level there is a directory, not a store.  For checks, if you are able to
     say, show me stores or units failing this check that are at this level then
     that would work.  Also realise that we show stats at various levels of a
     hierarchy, so not sure what that would need in the API.

   **TODO:** need to talk more about filtering stores. The discussion about
   filtering units is a different one.

   **TODO:** need to talk about filtering at other levels (not store, not unit).


Unit related
^^^^^^^^^^^^

+-----------+---------------+--------+--------------------------+------------+
| Command   | Description   | Method | URL                      | Needed for |
+===========+===============+========+==========================+============+
| list_all  | List all units| GET    | ``/stores/<STOR>/``      |            |
|           | in a file     |        |                          |            |
+-----------+---------------+--------+--------------------------+------------+
| list_units| Get a list of | GET    | ``/units/``              | [#virtaal]_|
|           | units that    |        |                          |            |
|           | match a       |        |                          |            |
|           | criterion     |        |                          |            |
+-----------+---------------+--------+--------------------------+------------+
| get_unit  | Retrieve a    | GET    | ``/units/<UNIT>/``       | [#virtaal]_|
|           | unit for      |        |                          |            |
|           | translation   |        |                          |            |
+-----------+---------------+--------+--------------------------+------------+
| translate | Provide or    | PATCH  | ``/units/<UNIT>/``       | [#virtaal]_|
|           | change a      | or PUT |                          |            |
|           | translation   |        |                          |            |
|           | for a unit    |        |                          |            |
+-----------+---------------+--------+--------------------------+------------+


.. note::
   * **Q:** Are we going to allow deleting/adding Units using the API?
   * **A:** No, at least for now. Units though would be added/deleted based on a
     store upload.


.. warning:: **TODO**: Criterion would include:

   * Search -- match (regex?) in source, target, location, comments

     **NOTE:** none of the following has been tested.

     * Starts with: ``/units/?target__startswith=window``
     * Contains (insensitive): ``/units/?source__icontains=window``
     * Ends with (insensitive): ``/units/?location__iendswith=window.py``
     * Match with regex: ``/units/?comments__regex=r'^(An?|The) +'``
     * Other https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups

   * Completion -- translated, untranslated, fuzzy (other XLIFF states or format
     specific states?)

     * Obsolete: ``/units/?state=-100``
     * Untranslated: ``/units/?state=0``
     * Fuzzy: ``/units/?state=50``
     * Translated: ``/units/?state=200``

   * Check -- failing checks

     **TODO:** need to see how to implement this.

   * Untranslated units from some deeper level in the hierarchy.

     **TODO:** need to see how to implement this.

   There are some others that we haven't implemented in Pootle e.g. Units that
   belong to a certain goal.  Julen's user page work exposes things like units
   that have suggestions, units that I translated, units that where overwritten
   by someone else.

   **TODO:** Does Pootle have goals?

   **TODO:** Will need time to complete that list of filters.

   **TODO:** For all this is necessary to first implement
   http://django-tastypie.readthedocs.org/en/latest/resources.html#basic-filtering


Suggestion related
^^^^^^^^^^^^^^^^^^

+-----------+---------------+--------+--------------------------+------------+
| Command   | Description   | Method | URL                      | Needed for |
+===========+===============+========+==========================+============+
| list_sugg | List all      | GET    | ``/units/<UNIT>/``       |            |
|           | suggestions   |        |                          |            |
|           | for a unit    |        |                          |            |
+-----------+---------------+--------+--------------------------+------------+
| suggest   | Provide a     | POST   | ``/suggestions/``        | [#virtaal]_|
|           | suggestion    |        |                          |            |
|           | for a unit    |        |                          |            |
+-----------+---------------+--------+--------------------------+------------+
| show      | Show a        | GET    | ``/suggestions/<SUGG>/`` |            |
|           | suggestion    |        |                          |            |
+-----------+---------------+--------+--------------------------+------------+
| suggest   | Change an     | PATCH  | ``/suggestions/<SUGG>/`` |            |
|           | existing      | or PUT |                          |            |
|           | suggestion    |        |                          |            |
|           | for a unit    |        |                          |            |
+-----------+---------------+--------+--------------------------+------------+
| reject    | Reject a      | DELETE | ``/suggestions/<SUGG>/`` |            |
|           | suggestion    |        |                          |            |
+-----------+---------------+--------+--------------------------+------------+


.. note::
   * **Q:** Are we going to accept/reject Suggestions using the API?
   * **A:** Not in the immediate future.  But I could imagine an Android app
     that makes it easy to review suggestions from volunteers.


.. warning::
   * Stats about suggestions,
   * Find all suggestions matching some criterion.

   **TODO:** Need to clarify this two items raised by Dwayne.


.. rubric:: Command footnotes

.. [#moz] Needed by Mozilla
.. [#solas] Needed for Solas integration
.. [#virtaal] Using Virtaal to translate offline
.. [#saas] Delivering Pootle as a service


Django side
-----------
We'll use `tastypie <http://tastypieapi.org/>`_ to handle the RESTful API.

- Authentication -- Will use BasicHTTPAuth. More methods can be added in the
  future.

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
