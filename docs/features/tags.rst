.. _tags:

Tags
====

.. versionadded:: 2.5.1

Pootle supports tags that can be used as a way to group related items and allow
filtering of them.

.. note::
    Currently tags can only be added to translation projects or individual
    files.


.. _tags#manage:

Managing tags
-------------

Tags are hidden by default, and can be shown by clicking on the |icon:icon-tag|
icon near the top of the page (in pages that allow showing the tags like
project overview, translation project overview, and so on). Clicking on it
again will hide the tags.

When tags are shown, an |icon:icon-tag-add| icon will be displayed (for users
who have enough permissions to add tags). Clicking on that icon will bring up a
form where tag name can be typed. If the tag doesn't exist yet it will be
created and then applied to the current item. Tag names are case insensitive
(they will be automatically converted to lowercase), they must be composed of
only letters and numbers, and can have spaces, colons, hyphens, underscores,
slashes or periods in the middle, but not at start or at the end.

Hovering over any of the tags with the mouse will show an "×" icon that can be
clicked to remove the tag.


.. _tags#filter:

Filtering tags
--------------

In project overview page, translation projects can be filtered by their tags.
Clicking on the |icon:icon-filter| icon (near the top of the page), will
activate tags filtering widget where existing tags can be selected to filter
the translation projects. Clicking on the |icon:icon-filter| icon again will
hide the filtering widget and reset the filters.
