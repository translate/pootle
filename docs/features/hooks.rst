.. _hooks:

Hooks
=====

Pootle supports hooks to customise behaviour on submit and update from
:doc:`Version Control Systems <version_control>`. They are Python scripts and
can do things like checking or converting formats before commit.


.. _hooks#notes:

Notes
-----

For Pootle 2.2, hooks will have to be rewritten:

- They need to take into account that VCS checkouts/clones are not separate, in
  *settings.VCS_DIRECTORY*

- Paths are given relative to the root of the *podirectory*.
