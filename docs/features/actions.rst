.. _actions:

Extension Actions
=================

Pootle supports extension actions that can be used to add custom action links
within the standard Pootle UI.

Extension actions are Python scripts and can do things like generating language
packs for download or performing checks across several languages and returning
a report.

.. _actions#implementing:

Implementing an extension action
--------------------------------

Extension actions are Python classes in module files stored in the
*pootle/scripts/actions* directory.  The name of the module or classes is not
important, but the class(es) defined in a module must be subclasses of the
ExtensionAction class.

There are several subclasses of ExtensionAction defined, depending on the scope
of the action.

* ProjectAction is used when the action will apply to all or part of a project.
* LanguageAction is used when the action will apply to a language across
  multiple projects
* TranslationProjectAction is used when the action will apply to a single
  language within a project
* StoreAction is used when the action will apply only to a single translation
  file (store) within a specific language and project

.. _actions#properties:

Extension Action properties
---------------------------

Every extension action has a category and a title.  The category is used to
group related actions together, and is displayed as a small text label on the
left margin of the **Actions** section of the relevant Pootle screens.  The
built-in actions for downloading and uploading translation files and archives
use the category 'Translate offline' but extension actions can use any category
they wish to.  The title of the extension action is the text of the link that
is displayed to the right of the category label, and clicking on that link will
invoke the action with the current project, language, and/or store.

.. _actions#tooltips

Extension action tooltips
-------------------------

The docstring for an extension action class is used as the tooltip (mouseover
text) for the link created.  Like all the other strings in an extension actions
module, it too is implicitly internationalized, and can be localized by
creating translation files and importing them into Pootle.

.. _actions#localization

Localization of categories and titles
-------------------------------------

It may be desirable to have the category and title text displayed in different
languages depending on the preferences of users.  If either property is a
string that is already in the Pootle localization (e.g. 'Translate offline') it
will be displayed using the standard Pootle localization for the current locale
selected by the user preferences.

Titles and categories that are not already localized (or for which a different
localization is desired) should be extracted from the extension action module
using the ``i18n`` script located in the ``pootle/scripts/ext_actions``
directory:

.. code-block:: bash
    $ cd $POOTLE_HOME/pootle/scripts/ext_actions
    $ ls
    hello.py    i18n
    $ ./i18n hello
    $ ls
    hello.pot   hello.py    i18n
 
The generated *module***.pot** file is a translation template file that can be
copied to a subdirectory for the language code, e.g. pootle/scripts/actions/fr
and localized there using Pootle, Virtaal, or any other translation tool that
works with PO files.

