.. _glossary:

Glossary
========

Translation Store
  A file that stores translations (e.g. a PO file) — although it could also be
  used to refer to other ways of storing translations.

  Contains a number of Translation Units, which contain messages.

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

Language
  They refer to the languages translated into.

Project
  They refer to the different programs/sets of messages we translate.

Translation Project
  A set of translation stores translating a project into a language.

Template
  A translation file that contains only the source or original texts.
