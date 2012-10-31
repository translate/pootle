.. _searching:

Searching in Pootle
===================

Pootle provides a searching functionality that allows translators and reviewers
to search through translations for some text. The search box is shown close to
the top of the page. Searching can be used to find specific things you want to
work on, see how issues were solved before, or to verify consistency in your
translations.

Search results are up to date, and will reflect the current translations in
Pootle. 


.. _searching#search_domain:

Search domain
-------------

It is important to realize that when a new search term is entered, **searching
will take place inside the currently viewed domain**. If you are currently at
the top level of your project, the whole project will be searched. If you are
viewing a directory, only files in that directory will be searched. If you are
already viewing/translating a file, only that file will be searched.

The first result will be shown in context in the file where it is found. When
you click "Skip", "Suggest" or "Translate" it will provide the next match to
the search (in the original domain) until all matches were presented. Remember
that if you edit the search query while viewing search results in a specific
file, your new query will only search in that specific file.


.. _searching#advanced_search:

Advanced search
---------------

The search function improved in Pootle 1.2. Next to the search textbox, there's
an arrow icon that when clicked will toggle some options for the search to be
done.

At this stage, the advanced search option allows **searching in specific
fields**. It is possible to select to search for text in source and target
texts as well as in comments and locations. Any combination of these options is
accepted.

As a default, it will search for source and target strings. If a non-default
search is performed, the search widget will slightly change its background
colour.


.. _searching#=_backend:

Backend
^^^^^^^

The basic searching uses :ref:`pogrep <toolkit:pogrep>` which will look for the
substring in the source and target text. It supports Unicode normalization.
Alternatively, a Pootle server might be installed with an :doc:`indexing engine
<../server/indexing>` (PyLucene or Xapian) to speed up searching. Search
results can differ slightly from the normal search, based on the indexing that
engine uses.

Some basic query in Lucene syntax is also possible. More information on `Lucene
queries <http://lucene.apache.org/java/docs/queryparsersyntax.html>`_.
