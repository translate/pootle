.. _tags:

Tags
====

.. versionadded:: 2.5.1

Pootle supports tags that can be used as a way to group and filter related
items.

.. note::
    Currently tags are only available for translation projects and individual
    files.  We expect this to expand in future versions.


.. _tags#manage:

Managing tags
-------------

Tags are hidden by default, and can be shown by clicking on the |icon:icon-tag|
tag icon near the top of the page (in pages that allow showing the tags like
project overview, translation project overview, and so on). Clicking on it
|icon:icon-tag| again will hide the tags.

When tags are shown, the |icon:icon-tag-add| add tag icon will be displayed
(for users who have enough permissions to add tags). Clicking on the icon will
allow you to add a new tag to the item. If the tag does not exist then one will
be created and applied to the current item.

.. note:: Tag names are case insensitive (they will be automatically converted
   to lowercase).

.. warning:: Tags must be composed of only letters and numbers, and can have
   spaces, colons, hyphens, underscores, slashes or periods in the middle, but
   not at start or at the end.

Hovering over any of the tags with the mouse will show the "x" icon that can be
clicked to remove the tag.

.. FIXME replace "x" with the real select2 icon


.. _tags#filter:

Filtering tags
--------------

On the project overview page, translation projects can be filtered based on
their tags.  Clicking on the |icon:icon-filter| filter icon (near the top of
the page), will activate tag filtering.  Use the tag filtering area to filter
the list of translation projects.  Clicking on the |icon:icon-filter| icon
again will hide the filtering widget and reset the filters.
