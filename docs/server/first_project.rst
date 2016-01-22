.. _first_project:

Your First Project
==================

Congratulations to your excellent choice of Pootle to manage your translations.
We hope you'll enjoy your swift transcendance into i10n with the Pootle crew.

Now that you have the server set up, it's time to create some messages to go with
your very special software. Most likely you have already a set of default messages
which you want to translate into a second language. This guide will help you get
started with these translations.

Pootle is a hybrid databse-and-files application, in that is both saves metadata
in the database, and files on disk. While this might change in the future, as Pootle
moves towards its own internal format, it is the case at the time of writing.

You can either choose to create the relevant folders yourself and have Pootle pick
the project up, or you can use add the *Template* language to your project. But
first! – let's add a new project.

In the top-right menu of the interface, you should see your newly created administrator
user (it's only a congruent-character if you're on a small screen). From the fold-out
drop down menu, choose *Admin* (in red) to get to the administration interface.

Under the *Projects* tab, you'll find a button called *New Project* to the top right,
just below the main menu that has your user-name. Click the button.

You're standing in a grotto and see a list of GUI elements. What do you do?

> type project details into GUI elements

A button labelled *Save* is greyed in.

> click it

You are standing in a grotto, but now with a different list of GUI elements and a few
unobtrusive links at the bottom. One link is *Languages*. What do you do?

> click it

You're now faced with an interface that gives you an error message, that there's no
"Template" defined. You peruse the docs for a few hours, but fail to find mentions
of how to capture the elusive Template.

After voyaging to the gitter chat, you are granted a seans with a ancient pootle-master,
called Dwayne. It turns out that you should create the folder structure as such;

POOTLE_TRANSLATION_DIRECTORY/my-react-project/fr.po

Where POOTLE_TRANSLATION_DIRECTORY is defined as such in pootle.conf:
`POOTLE_TRANSLATION_DIRECTORY=working_path('translations')`, so you create a tree like this:

`./translations/my-project/en.xliff`

The GUI/server should automatically take in these changes, but doesn't. If it doesn't, then
you can poke it with a stick: `pootle update_stores --project=my-project --config=pootle.conf`.

It still won't update, however, and the ancient master has left the house.
