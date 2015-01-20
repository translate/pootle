.. _glossary:

Glossary
========


.. _glossary#store:

Translation Store
  A file that stores translations (e.g. a PO file) — although it could also be
  used to refer to other ways of storing translations.

  Contains a number of Translation Units, which contain messages.


.. _glossary#unit:

Translation Unit
  At the simplest level contains a single **source** string (the original
  message) and a single **target** string (the translated message).

  XLIFF refers to this as a unit, Gettext calls it a message or string.  Some
  industry tools talk of segments.  To maintain consistency we refer to
  **string** in the GUI and **unit** in the code.

  Monolingual formats (like .properties, OpenOffice SDF, DTD, HTML, etc.) only
  contain a source strings.

  However when handling plurals the source may actually contain different
  variants of a message for different plural forms (e.g. in English, the
  singular and plural), and the target as well (the number of variants in
  source and target strings are often different because different languages
  handle plurals differently).


.. _glossary#language:

Language
  They refer to the languages translated into.


.. _glossary#project:

Project
  They refer to the different programs/sets of messages we translate.


.. _glossary#translation-project:

Translation Project
  A set of translation stores translating a project into a language.


.. _glossary#template:

Template
  A translation file that contains only the source or original texts.


.. _glossary#translation_states:

Translation States
------------------

.. _glossary#untranslated:

Untranslated
  A unit that is not translated i.e. blank.


.. _glossary#incomplete:

Incomplete
  See: Needs Attention i.e. Untranslated + Fuzzy


.. _glossary#translated:

Translated
  The unit has a translation.


.. _glossary#fuzzy:

Fuzzy
  In Gettext PO fuzzy means that a unit will needs to be reviewed and will not
  be used in production. On Pootle for the user we call this 'Needs Work' as
  the term fuzzy is either technical for some users, or confusing to those who
  use the term fuzzy for Translation Memory, as in 'fuzzy match'.


.. _glossary#needs_work:

Needs work
  See: Fuzzy


.. _glossary#needs_review:

Needs review
  Currently see: Fuzzy
  In the future this will actually mean that the translated string still requires review.


.. _glossary#needs_attention:

Needs attention
  Untranslated + Fuzzy


.. _glossary#pootle-internals:

Pootle internals
----------------

.. _glossary#context-object:

Context object (``ctx_obj``)
  An object representing the context that encloses the current view.

  If we are navigating through the files for an existing translation project,
  the context object will refer to the current translation project.

  Similarly, if we are in the overview page for a language, the context will
  point to the current language object. In the overview page for a project, the
  context object points to the current project.

  At a higher level, the root directory is considered the context object.


.. _glossary#resource-object:

Resource object (``resource_obj``)
  An object representing the resource that the current view is referring to.

  For example, if we are navigating through the files and directories for an
  existing translation project, the resource object will refer to the current
  file or directory object.

  If the current view refers to multiple resources, the resource object is the
  same as the context object.
