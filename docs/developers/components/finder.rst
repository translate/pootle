#doctest: +ELLIPSIS
.. _translation_file_finder:


Translation File Finder
=======================

This tool provides a way of mapping translation files in a filesystem to pootle codes for
``Language`` and ``Directory`` as well as ``filename`` and ``extension``.

For a given translation path it will scan a filesystem looking for matching files, and
returning the match information.

Translation paths are given in the format

::

   /path/to/my/translation/resources/<dir_path>/<language_code>/<filename>.<ext>

At a minimum a path must have a ``<language_code>`` tag and end with ``.<ext>``

Paths are matched using a regex, and the `dir_path`, `lang` and `filename`
matches can be read from the results.


Retrieving a Translation file finder
------------------------------------

The finder should be given an absolute file path.

.. code-block:: python

   >>> from pootle_fs.finder import TranslationFileFinder
   >>> finder = TranslationFileFinder("/path/to/<language_code>.<ext>")
   >>> finder
   <pootle_fs.finder.TranslationFileFinder object at ...>


Matching a simple filepath
--------------------------

This will match a file and interpret the filename without the ext as the language, if the file matches.

.. code-block:: python

   >>> found = finder.match("/path/to/foo.po")

The match method returns a tuple, the first part is the matched path

   >>> found[0]
   '/path/to/foo.po'


The second part is a match dictionary, containing the matched parts, which can be mapped to codes in Pootle.


   >>> type(found[1])
   <type 'dict'>

   >>> sorted(found[1].keys())
   ['dir_path', 'ext', 'filename', 'language_code']
   >>> found[1]["language_code"]
   'foo'
   >>> found[1]["ext"]
   'po'


If the `<filename>` tag is not used, the filename is taken from the filename on the filesystem.

In this case that is also the ``<language_code>``

.. code-block:: python

   >>> found[1]["filename"]
   'foo'
   >>> found[1]["language_code"]
   'foo'

   >>> finder.match("/path/to/some-foo.po")[1]["filename"]
   'some-foo'
   >>> finder.match("/path/to/some-foo.po")[1]["language_code"]
   'some-foo'

   >>> finder.match("/path/to/another_foo.po")[1]["filename"]
   'another_foo'
   >>> finder.match("/path/to/another_foo.po")[1]["language_code"]
   'another_foo'


The translation path does not include any subdirectories, so this does not match

.. code-block:: python

   >>> finder.match("/path/to/bar/foo.po") is None
   True


Matching a filepath with filename
---------------------------------

With the following examples, the matcher will look for a section to use in Pootle as the filename

.. code-block:: python

   >>> finder = TranslationFileFinder("/path/to/<language_code>/<filename>.<ext>")

This will not match, because it must match both the lang and filename.

.. code-block:: python

   >>> finder.match("/path/to/foo.po") is None
   True

But this will match both filename and lang.

.. code-block:: python

   >>> sorted(finder.match("/path/to/foo/bar.po")[1].items())
   [('dir_path', ''), ('ext', 'po'), ('filename', 'bar'), ('language_code', 'foo')]


Translation paths can be structured according to requirements

.. code-block:: python

   >>> finder = TranslationFileFinder("/path/to/<language_code>/some/other/<filename>.<ext>")

   >>> finder.match("/path/to/foo/bar.po") is None
   True

   >>> sorted(finder.match("/path/to/foo/some/other/bar.po")[1].items())
   [('dir_path', ''), ('ext', 'po'), ('filename', 'bar'), ('language_code', 'foo')]


The elements can appear in any order, and anywhere in the translation path.

.. code-block:: python

   >>> finder = TranslationFileFinder("/path/to/<filename>/some/<language_code>/other.<ext>")
   >>> sorted(finder.match("/path/to/foo/some/bar/other.po")[1].items())
   [('dir_path', ''), ('ext', 'po'), ('filename', 'foo'), ('language_code', 'bar')]


.. code-block:: python

   >>> finder = TranslationFileFinder("/path/to/some-<filename>/other-<language_code>/filename.<ext>")
   >>> sorted(finder.match("/path/to/some-foo/other-bar/filename.po")[1].items())
   [('dir_path', ''), ('ext', 'po'), ('filename', 'foo'), ('language_code', 'bar')]


Matching a directory path
-------------------------


You can also match a directory path.

.. code-block:: python

   >>> finder = TranslationFileFinder("/path/to/<dir_path>/<language_code>.<ext>")
   >>> sorted(finder.match("/path/to/some/foo.po")[1].items())
   [('dir_path', 'some'), ('ext', 'po'), ('filename', 'foo'), ('language_code', 'foo')]


This can include ``/`` s.

.. code-block:: python

   >>> sorted(finder.match("/path/to/some/other/foo.po")[1].items())
   [('dir_path', 'some/other'), ('ext', 'po'), ('filename', 'foo'), ('language_code', 'foo')]


And you can match a filename at the same time

.. code-block:: python

   >>> finder = TranslationFileFinder("/path/to/<dir_path>/<language_code>/translation-file.<ext>")
   >>> sorted(finder.match("/path/to/some/foo/translation-file.po")[1].items())
   [('dir_path', 'some'), ('ext', 'po'), ('filename', 'translation-file'), ('language_code', 'foo')]

   >>> sorted(finder.match("/path/to/some/other/foo/translation-file.po")[1].items())
   [('dir_path', 'some/other'), ('ext', 'po'), ('filename', 'translation-file'), ('language_code', 'foo')]


Filtering with glob filters
---------------------------

You can use glob style pattern matching to filter matches.

.. code-block:: python

   >>> finder = TranslationFileFinder(
   ...     "/path/to/<dir_path>/<language_code>/translation-file.<ext>",
   ...     path_filters=["/path/to/dir1/*"])


   >>> sorted(finder.match("/path/to/dir1/foo/translation-file.po")[1].items())
   [('dir_path', 'dir1'), ('ext', 'po'), ('filename', 'translation-file'), ('language_code', 'foo')]


Which would exclude dir2

.. code-block:: python

   >>> finder.match("/path/to/dir2/foo/translation-file.po") is None
   True


File extensions
---------------

By default the matcher will match either ``.po`` or ``.pot``

.. code-block:: python

   >>> finder = TranslationFileFinder("/path/to/<language_code>.<ext>")

   >>> sorted(finder.match("/path/to/foo.po")[1].items())
   [('dir_path', ''), ('ext', 'po'), ('filename', 'foo'), ('language_code', 'foo')]

   >>> sorted(finder.match("/path/to/foo.pot")[1].items())
   [('dir_path', ''), ('ext', 'pot'), ('filename', 'foo'), ('language_code', 'foo')]


But you can match alternate extensions if you require.

.. code-block:: python

   >>> finder = TranslationFileFinder("/path/to/<language_code>.<ext>", extensions=["abc", "xyz"])

   >>> finder.match("/path/to/foo.po") is None
   True

   >>> sorted(finder.match("/path/to/foo.abc")[1].items())
   [('dir_path', ''), ('ext', 'abc'), ('filename', 'foo'), ('language_code', 'foo')]
   
   >>> sorted(finder.match("/path/to/foo.xyz")[1].items())
   [('dir_path', ''), ('ext', 'xyz'), ('filename', 'foo'), ('language_code', 'foo')]



Walking a filesystem
--------------------

Lets create a temporary file

.. code-block:: python

   >>> import os
   >>> import tempfile
   >>> tmpdir = tempfile.mkdtemp()
   >>> open(os.path.join(tmpdir, "foo.po"), "w").write("")
   >>> open(os.path.join(tmpdir, "bar.po"), "w").write("")
   >>> open(os.path.join(tmpdir, "baz.xliff"), "w").write("")
   >>> finder = TranslationFileFinder(os.path.join(str(tmpdir), "<language_code>.<ext>"))

The finder with ascertain the file root, ie the directory that it should look in.

.. code-block:: python

   >>> finder.file_root == str(tmpdir)
   True

You can walk the filesystem from the finder.file_root. This will return the filepaths regardless
of whether they match

.. code-block:: python

   >>> finder.walk()
   <generator object walk at ...>

   >>> sorted(os.path.basename(f) for f in finder.walk())
   [u'bar.po', u'baz.xliff', u'foo.po']


To find matching files, use finder.find

.. code-block:: python

   >>> finder.find()
   <generator object find at ...>

It should just find the 2 po files

.. code-block:: python

   >>> sorted(os.path.basename(path) for path, match in finder.find())
   [u'bar.po', u'foo.po']


Reverse matching
----------------

Given a ``language``, and optionally ``dir_path``, ``filename``, and ``ext`` the finder
can provide a reverse path according to its translation_path

It will use the first ext from the extension list, the default is ``.po``

.. code-block:: python


   >>> finder = TranslationFileFinder("/path/to/<language_code>.<ext>")

   >>> finder.reverse_match("foo")
   '/path/to/foo.po'


You can map it to another extension in the finders extensions list, by default this includes ``.pot``

.. code-block:: python

   >>> finder.reverse_match("foo", extension="pot")
   '/path/to/foo.pot'

But you cant use an ext not in the finders list

.. code-block:: python

   >>> import pytest

   >>> with pytest.raises(ValueError):
   ...     finder.reverse_match("foo", extension="abc")


If the translation_path includes ``filename`` but you don`t specify it
the matcher will reuse the ``lang``

.. code-block:: python

   >>> finder = TranslationFileFinder("/path/to/<language_code>/<filename>.<ext>")
   >>> finder.reverse_match("foo")
   '/path/to/foo/foo.po'

Or you can set it as required

.. code-block:: python

   >>> finder.reverse_match("foo", filename="bar", extension="pot")
   '/path/to/foo/bar.pot'


And you can set the ``dir_path`` too

.. code-block:: python

   >>> finder = TranslationFileFinder("/path/to/<dir_path>/<language_code>/<filename>.<ext>")


Which is optional when reverse matching


.. code-block:: python

   >>> finder.reverse_match("foo", filename="bar", extension="pot")
   '/path/to/foo/bar.pot'

   >>> finder.reverse_match("foo", filename="bar", extension="pot", dir_path="some/other")
   '/path/to/some/other/foo/bar.pot'
