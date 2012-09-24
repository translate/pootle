.. _administration:

Administration
==============

In default Pootle installations, an *admin* account (the password matches the
username) is created with superuser privileges which can be used to administer
the whole site.

.. note::

    It's highly recommended that you change the password for the default
    *admin* account on your first login, or even delete the account and
    assign superuser rights to another user.


.. _administration#scope:

Administration scope
--------------------

Users with administration privileges will have an extra *Admin* element within
the main navigation bar, which gives direct access to the administration
functions of the site.

Administrators can change the general settings for the site (such as the server
title or description), as well as add, edit, and remove users, languages, and
translation projects. They are also able to define the default permissions that
will apply to the whole site unless otherwise noted.

Apart from that, administrators have full rights over all the translation
projects, so they can do whatever can be done: translate, suggest, upload new
files, update VCS checkouts, ...


.. _administration#adding_new_site_administrators:

Adding new site administrators
------------------------------

If you want to assign site administration permissions to an already existing
user, just go to the *Users* tab within the *Administration* page, check
the *Superuser status* checkbox for the user you want to make administrator
and click on *Save Changes*. That's all!


.. _administration#language_administrators:

Language administrators
-----------------------

Administration rights can be delegated for all tasks within a language. This
allows the language administrator to set permissions in the language, set
permissions in certain projects in the language, manage files, etc.

To appoint a language administrator, visit the language page, and add the
administration right on the *Permissions* tab.
