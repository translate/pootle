.. _goals:

Goals
=====

.. versionadded:: 2.5.1

Pootle supports goals that can be used as a way to group items based on any
random criteria, prioritize work on those items and allow an easy translation
of those groups of items.

Pootle allows not only to apply goals directly to files, but also to apply a
goal to a given file across all the languages in a project by using the so
called :ref:`project goals <goals#regular-vs-project>`.

.. note::
    Currently goals can only be applied to individual files.


.. _goals#regular-vs-project:

Regular goals vs project goals
------------------------------

Pootle supports two types of goals:

* *Regular goals* (or just goals)
* *Project goals*

The difference among these two types is that project goals allow to apply them
to a given store project-wide by applying them to the chosen store in the
*template* translation project. This saves project managers a lot of time,
specially when the project hosts a lot of languages.

The goal type can be easily changed using the :ref:`editing form <goals#edit>`.

Project goals are shown below the regular ones in the :ref:`goals tab
<goals#tab>`. The statistics for a project goal in a translation project only
include the matching stores, and won't be displayed at all if the goal doesn't
have any matching store.


.. _goals#tab:

Goals tab
---------

The goals tab is shown on the overview page for any translation project with
goals applied to any of its stores. If the tab is shown, when clicking on it a
comprehensive list of all the goals in that translation project is displayed,
including stats for each goal and links for translating it or review its
suggestions.

The goals tab is also displayed on any directory inside a translation project,
if there is any goal applied to stores inside that directory, or in
subdirectories inside it. In this case the goal list that is displayed is
restricted to only those goals.


.. _goals#drill-down:

Drill down in a goal
++++++++++++++++++++

It is possible to drill down on each goal on the goals tab and see the file
tree for the stores that belong to that goal. This is just like the regular
files view with some small differences:

* In the upper level there is a **..** link that points to the goals tab, that
  allows to get out of the drill down view,
* The breadcrumbs includes a reference to the current goal,
* Every translate link in the table points to a translate view restricted to
  the goal that is currently being inspected.


.. _goals#apply:

Apply and unapply goals
-----------------------

Goals are just special tags whose name starts with **goal:** (including the
colon) and that have some additional attributes, like a priority.

Like tag names, the goal names are case insensitive (they are automatically
converted to lowercase), and must be composed of only letters and numbers, and
can have spaces, colons, hyphens, underscores, slashes or periods in the
middle, but not at start or at the end.

Goals can be applied and unapplied to stores using the same method that can be
used for :ref:`adding and removing tags <tags#manage>`. If the applied goal
didn't previously exist then it is created. Unapplying a goal doesn't actually
remove it, but unbinds it from the store.

.. note::
    Remember that goals are special tags with names starting with **goal:**
    (including the colon). So if its name starts with any other string a tag
    will be created instead.


.. _goals#edit:

Edit goals
----------

You will likely need to tweak newly added goals, or sometimes any already
existing goals, for example to change its priority or make it be a *project 
goal*.

In order to do that you must go to the drill down view for that goal and use
the form in the *Description* section.

.. note::
    Keep in mind that if the goal is not applied to any store then it is not
    possible to edit it because it doesn't have no drill down view.


.. _goals#translate:

Translating goals
-----------------

In the goals tab and in the drill down views for each goal are displayed
several links that point to the translation editor. Each link allows to
translate units (needing work or not) or review existing suggestions.

Once in the translation editor the different filters are restricted to the
stores in the given path that belong to the chosen goal, thus allowing the
translators to focus on a specific goal.
