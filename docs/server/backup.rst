.. _backup:

Backup your Pootle system
=========================

In particular you should backup:

- All your translation files (your whole
  :setting:`POOTLE_TRANSLATION_DIRECTORY`). Use the :djadmin:`sync_stores`
  command to synchronize all your translation files to disk before making any
  backup.

- Your settings, to avoid losing any settings customizations.

- Your complete database using the appropriate *dump*
  command for your database system. For example :command:`mysqldump` for MySQL,
  or :command:`pg_dump` for PostgreSQL.

- Any code, templates or styling customization that
  you have done to your installation.
