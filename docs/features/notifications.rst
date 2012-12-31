.. _notifications:

Notifications
=============

Pootle has RSS feeds for notifications about concrete translation projects,
languages or even the whole site. Pootle's front page will show the latest
events on the site.


.. _notifications#types_of_notifications:

Types of notifications
----------------------

Notifications can either be manual or automatic.

Manual notifications are written by the language or translation project
administrators and are shown in the relevant pages within the "News" tab.

When certain events occur, events will automatically be notified in the
relevant feeds. The events that generate notices include:

- New languages added

- New projects added

- New projects added to languages

- Project updated from version control

- Project updated against templates

- File committed to version control

- File uploaded to project

- Archive uploaded to project

- File reached 100%

- User registers in a language

- User registers in a project


If you want to receive all events for a language (including sub-projects) or
absolutely everything on the whole server, add ``?all=True`` to the end of the
URL for the RSS feed. (This is not currently advertised on Pootle due to
possible performance impact.)
