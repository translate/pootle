.. _searching:

Searching in Pootle
===================

Pootle provides search functionality that allows translators and reviewers to
search through translations for some text. The search box is shown close to the
top of the page. Searching can be used to find specific things you want to work
on, see how issues were solved before, or to verify consistency in your
translations.

Search results are up to date, and will reflect the current translations in
Pootle. 


.. _searching#search_domain:

Search domain
-------------

It is important to realize that when a new search term is entered, **searching
will take place inside the currently viewed domain**. If you are currently at
the top level of your project, the whole project will be searched. If you are
viewing a directory, only files under that directory will be searched. If you
are already viewing/translating a file, only that file will be searched.

The first result will be shown in context in the file where it is found. When
you click "Skip", "Suggest" or "Translate" it will provide the next match to
the search (in the original domain) until all matches were presented. Remember
that if you edit the search query while viewing search results in a specific
file, your new query will only search in that specific file.


.. _searching#advanced_search:

Advanced search
---------------

When you enter a search box a dropdown will open allowing you to limit or
expand your **search to specific fields**. Any combination of these fields and
options is accepted.

Fields that you can search in include:

- Source Text -- the original reference text.
- Target Text **(default)** -- the translations.
- Comments -- any comments with the translation.
- Location -- any location, key or ID value.

Options:

- Exact Match **(default: off)** -- search in a case sensitive manner. With
  this option on searching for "File" will not find "file".
