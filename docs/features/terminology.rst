.. _terminology:

Terminology
===========

Pootle can help translators with terminology. Terminology can be specified to
be global per language, and can be overridden per project for each language. A
project called *terminology* (with any full name) can contain any files that
will be used for terminology matching. Alternatively a file with the name
*pootle-terminology.po* (in a PO project) can be put in the directory of the
project, in which case the global one (in the terminology project) will not be
used. Matching is done in real time.

Ideally, the source term should be the shortest, simplest form of a word.
Therefore *cat*, *dog*, *house* are good, but *cats*, *dogged* and *housing*
are bad.

Context indicators are allowed in the source text, in brackets after the term,
but keep them short, eg *file (noun)*, *view (verb)*, etc.

The ideal is therefore that the target term be something that you'd like the
translator to be able to insert... but strictly speaking the target text can be
anything, including a definition.

If the terminology PO file has translator comments, they will be displayed as a
tooltip in Pootle.


.. _terminology#what_does_it_do:

What does it do?
----------------

If our glossary has an entry: *file->lêer*, and we translate a sentence like
*The file was not found*, we can suggest the glossary entry *file->lêer* as
relevant to the translation, even if we don't have any TM entry that is related
to the complete sentence that is available for translation.

Say our glossary has an entry *category->kategorie* and we translate a sentence
like *Please enter the categories for this photo*, we can suggest the glossary
entry *category->kategorie*, even though the letters *category* doesn't occur
anywhere in the original string.


.. _terminology#limits:

Limits
------

Currently a single term entry can be up to 30 characters long (including
context information), and the first 500 characters of each translation are
scanned. Terms can consist of many words, but consider making them as general
or simple as possible for maximum impact.

If these limits prove too restrictive, feel free to point out use cases where
this is not sufficient.

Since the terminology matching is performed in real-time, you might want to
keep an eye on the size of your terminology project to ensure that performance
is not affected too much by having too many terms. This is highly dependent on
your server abilities and the nature of what you are translating.
