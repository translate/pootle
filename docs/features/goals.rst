.. _goals:

Goals
=====

.. versionadded:: 2.5.1

Goals provide a way to group work based on any criteria.  They can be
prioritized to allow translators to focus on the most important work.

By using :ref:`project goals <goals#regular-vs-project>` goals can be applied
to the same file across all the languages in the project.

.. note::
    Currently goals can only be applied to individual files.


.. _goals#regular-vs-project:

Regular goals vs project goals
------------------------------

Pootle supports two types of goals:

#. *Regular goals* (or just goals)
#. *Project goals*

Project goals are available in all languages.  They are applied to files in the
*template* translation project. This allows project managers to easily define a
goal shared across all languages in the project.

The goal type can easily be changed using the :ref:`goal editing form
<goals#edit>`.

Project goals are shown below regular goals in the :ref:`goals tab
<goals#tab>`.

The statistics for a goal in a translation project will only include files that
are part of that goal, and won't be displayed at all if the goal doesn't have
any matching files in the current directory of the project.


.. _goals#tab:

Goals tab
---------

The goals tab is shown on the overview page for any translation project with
goals applied to any of its files. When shown, the goals tab provides a
comprehensive list of all the goals in that translation project, including
statistics for each goal and links for working on the translations.

The goals tab is also displayed on any directory, if there is any goal applied
to files inside that directory and its subdirectories.


.. _goals#drill-down:

Drill down into a goal
++++++++++++++++++++++

It is possible to drill down into each goal on the goals tab to see the files
and directories that belong to a goal. This works like the regular files view
with some small differences:

* In the upper level **..** will return you to the list of goals,
* Breadcrumbs includes a reference to the current goal,
* Every translate link in the table points to a translate view restricted to
  the goal that is currently being viewed.


.. _goals#apply:

Adding and removing files from a goal
-------------------------------------

Goals are special tags which start with **goal:** (including the colon) and
that have some additional attributes.

.. note:: Like tag names, the goal names are case insensitive (they are
   automatically converted to lowercase), and must be composed of only letters
   and numbers, and can have spaces, colons, hyphens, underscores, slashes or
   periods in the middle, but not at start or at the end.

.. note::
   If you create a goal without the **goal:** prefix then an ordinary tag will
   be created instead.

Goals can be added and removed from a file as you would :ref:`add and remove
tags <tags#manage>`. If the goal did not previously exist then a bew goal is
created.  While if you remove a goal from a file it will simply remove the
association of that file to the goal, the goal itself will not be removed.


.. _goals#edit:

Editing goals
-------------

To modify the properties of goals go to the goals tab and drill down into the
goal.  Use the form in the *Description* section to modify any of the goal
properties.

.. note::
   Remember that if the goal is not applied to any files then it is not
   possible to edit the goal, as you won't have access to it in the goals tab.
   Simply add a file to the goal and you will be able to edit the goal.

You can modify the goal description and turn it into a project wide goal as
needed.


.. _goals#translate:

Translating goals
-----------------

The goals tab and goals drill down views provide translation links as in the
normal file view that will take you to the translation editor. Each link allows
you to translate strings limited to the current goal.

Once in the translation editor the different filters are restricted to the
stores in the given path that belong to the chosen goal, thus allowing you to
focus on the work in the current goal.

