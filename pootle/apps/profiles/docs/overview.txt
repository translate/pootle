====================
Django user profiles
====================


This is a fairly simple user-profile management application for
Django_, designed to make the process of creating, editing and viewing
user profiles as painless as possible.

.. _Django: http://www.djangoproject.com/


Overview
========

In order to provide site-specific, per-user information in addition to
what's stored by the ``User`` model in ``django.contrib.auth``, Django
allows the use of a "user profile" model, which should be specified as
the value of the ``AUTH_PROFILE_MODULE`` setting. If you're unfamiliar
with this process, documentation is available in the "Profiles"
section of `Chapter 12 of the Django book`_. This application assumes
that you have created a profile model for use on your site, and that
you have filled in the ``AUTH_PROFILE_MODULE`` setting appropriately.

This application provides views which cover the primary aspects of
using profiles:

* Allowing users to create their profiles

* Allowing users to edit their profiles

* Allowing profiles to be publicly viewable

Of these, the first two are the most important; the third -- publicly
viewing user profiles -- is useful, but for sites which use profiles
merely to store user preferences this can usually be omitted.


.. _Chapter 12 of the Django book: http://www.djangobook.com/en/beta/chapter12/


Installation
============

In order to use django-profiles, you will need to have a
functioning installation of Django 1.0 or newer.

There are three basic ways to install django-profiles: automatically
installing a package using Python's package-management tools, manually
installing a package, and installing from a Mercurial checkout.


Using a package-management tool
-------------------------------

The easiest way by far to install django-profiles and most other
interesting Python software is by using an automated
package-management tool, so if you're not already familiar with the
available tools for Python, now's as good a time as any to get
started.

The most popular option currently is `easy_install`_; refer to its
documentation to see how to get it set up. Once you've got it, you'll
be able to simply type::

    easy_install django-profiles

And it will handle the rest.

Another option that's currently gaining steam (and which I personally
prefer for Python package management) is `pip`_. Once again, you'll
want to refer to its documentation to get up and running, but once you
have you'll be able to type::

    pip install django-profiles

And you'll be done.


Manually installing the 0.2 package
-----------------------------------

If you'd prefer to do things the old-fashioned way, you can manually
download the `django-profiles 0.2 package`_ from the Python
Package Index. This will get you a file named
"django-profiles-0.2.tar.gz" which you can unpack (double-click on
the file on most operating systems) to create a directory named
"django-profiles-0.2". Inside will be a script named "setup.py";
running::

    python setup.py install

will install django-profiles (though keep in mind that this
defaults to a system-wide installation, and so may require
administrative privileges on your computer).


Installing from a Mercurial checkout
------------------------------------

If you have `Mercurial`_ installed on your computer, you can also
obtain a complete copy of django-profiles by typing::

    hg clone http://bitbucket.org/ubernostrum/django-profiles/

Inside the resulting "django-profiles" directory will be a
directory named "profiles", which is the actual Python module for
this application; you can symlink it from somewhere on your Python
path. If you prefer, you can use the setup.py script in the
"django-profiles" directory to perform a normal installation, but
using a symlink offers easy upgrades: simply running ``hg pull -u``
inside the django-profiles directory will fetch updates from the
main repository and apply them to your local copy.


.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _pip: http://pypi.python.org/pypi/pip/
.. _django-profiles 0.2 package: http://pypi.python.org/pypi/django-profiles/0.2
.. _Mercurial: http://www.selenic.com/mercurial/wiki/


Basic use
=========

For default use, create a profile model for your site and specify the
``AUTH_PROFILE_MODULE`` setting appropriately. Then add ``profiles``
to your ``INSTALLED_APPS`` setting, create the appropriate templates
and set up the URLs. For convenience in linking to profiles, your
profile model should define a ``get_absolute_url()`` method which
routes to the view ``profiles.views.profile_detail``, passing the
username. Typically, this will be done as follows::

    def get_absolute_url(self):
        return ('profiles_profile_detail', (), { 'username': self.user.username })
    get_absolute_url = models.permalink(get_absolute_url)

In the default configuration, this application requires four
templates to be created:

``profiles/create_profile.html``
    This will display the form for users to initially fill in their
    profiles; it receives one variable -- ``form``, representing the
    form for profile creation -- directly, and also uses
    ``RequestContext`` so that context processors will be applied.

``profiles/edit_profile.html``
    This will display the form for users to edit their profiles; it
    receives one variable -- ``form``, representing the form for
    profile editing -- directly, and also uses ``RequestContext`` so
    that context processors will be applied.

``profiles/profile_detail.html``
    This will publicly display a user's profile; it receives one
    variable -- ``profile``, representing the profile object --
    directly, and also uses ``RequestContext`` so that context
    processors will be applied.

``profiles/profile_list.html``
    This will display a list of user profiles, using `the
    list_detail.object_list generic view`_.

For the default URL setup, add the following line to your root
URLConf::

   (r'^profiles/', include('profiles.urls')),

This will set up the following URL patterns:

* ``/profiles/create/`` will be the view for profile creation, and its
  URL pattern is named ``profiles_create_profile``.

* ``/profiles/edit/`` will be the view for profile editing, and its
  URL pattern is named ``profiles_edit_profile``.

* ``/profiles/<username>/`` will be the view for public display of a
  user profile, and its URL pattern is named
  ``profiles_profile_detail``.

* ``/profiles/`` will be the view for a browsable list of user
  profiles.

For notes on more advanced usage, including customization of the form
classes used for profile editing and creation and how to allow users
to prevent public display of their profiles, see the file
``views.txt`` in this directory.

.. _the list_detail.object_list generic view: http://www.djangoproject.com/documentation/generic_views/#django-views-generic-list-detail-object-list

If you spot a bug
=================

Head over to this application's `project page on Bitbucket`_ and
check `the issues list`_ to see if it's already been reported. If not,
open a new issue and I'll do my best to respond quickly.

.. _project page on Bitbucket: http://www.bitbucket.org/ubernostrum/django-profiles/overview/
.. _the issues list: http://www.bitbucket.org/ubernostrum/django-profiles/issues/
