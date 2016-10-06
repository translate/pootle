.. _pootle_fs_statuses:

Pootle FS statuses
==================

Pootle FS uses a set of statuses for the files or stores it manages, using
these it is able to determine what to do to resolve the scenario.

There are two groups of statuses:

* Unstaged - these need to be resolved by the user and will become staged.
* Staged - staged and ready to be `sync`'ed.


Unstaged statuses
-----------------

Statuses that need an action to be specified in order for Pootle FS to be able
to resolve them:


``conflict``
  Both the Pootle store and the filesystem file have changed. To resolve this
  conflict use :djadmin:`merge` to merge the two and manage conflict
  resolution. Or if you wish to discard one or the other use :option:`fetch
  --force <fetch --force>` or :option:`add --force <add --force>` to keep the
  filesystem version or Pootle version respectively.

``conflict_untracked``
  Conflict can also arise if both the store and file are untracked. In this
  case you can use :djadmin:`merge` to combine the translation and manage
  conflict resolution for each unit. Or to force taking the whole file or store
  use either :option:`fetch --force <fetch --force>` or :option:`add --force
  <add --force>` depending on whether you want to keep the filesystem file or
  the Pootle store.

``pootle_untracked``
  A new store has been added in Pootle but does not have any matching file on
  the filesystem. You can use either :djadmin:`add` to create the file on the
  filesystem and push the translations on the store to it, or alternatively use
  :djadmin:`rm` to stage the store for removal.

``fs_untracked``
  A new file has been added in the filesystem but does not have any matching
  store in Pootle. You can use either :djadmin:`fetch` to pull the file into
  Pootle or alternatively use :djadmin:`rm` to stage the file for removal.

``pootle_removed``
  A tracked store has been removed. Either use :option:`fetch --force
  <fetch --force>` to restore the filesystem version, or use :djadmin:`rm` to
  stage for removal from filesystem.

``fs_removed``
  A tracked file has been removed from the filesystem. Either use :option:`add
  --force <add --force>` to restore the Pootle version, or use :djadmin:`rm` to
  stage for removal from Pootle.


Staged statuses
---------------

These statuses reflect changes that can be either unstaged by using
:djadmin:`unstage` or executed with :djadmin:`sync`:


``pootle_ahead``
  A Pootle store has changed since the last synchronization. Running
  :djadmin:`sync` will push the changes to the filesystem.

``fs_ahead``
  A file has changed in the filesystem since the last synchronization. Running
  :djadmin:`sync` will pull the changes to Pootle.

``pootle_staged``
  A new store (with no associated file on the filesystem) has been created in
  Pootle and has been staged to be added to the filesystem. Running
  :djadmin:`sync` will create the file on the filesystem.

``fs_staged``
  A new file (with no associated store on Pootle) has been created in the
  filesystem and has been staged to be added to Pootle. Running :djadmin:`sync`
  will create the store on Pootle.

``merge_pootle_wins``
  Merge stores or files that have both been updated. If there are conflicts use
  the translation from Pootle and turn the translation from the file into a
  suggestion.

``merge_fs_wins``
  Merge stores or files that have both been updated. If there are conflicts use
  the translation from the filesystem and convert the translation from Pootle
  into a suggestion.

``remove``
  A file or store, whose corresponding store or file is missing, has been
  staged for removal. Running :djadmin:`sync` will remove the file or store.

``both_removed``
  A previously tracked file has been staged to be removed from both the
  filesystem and Pootle. Running :djadmin:`sync` will remove both the file and
  store.
