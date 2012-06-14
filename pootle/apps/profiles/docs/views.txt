==================
User profile views
==================


This application provides four views related to the creation, editing
and display of user profiles, which cover most aspects of the common
case of using profiles. All of these views are configurable to varying
extents via keyword arguments.


``profiles.views.create_profile``
=================================

Create a profile for the current user, if one doesn't already exist.

If the user already has a profile, as determined by
``request.user.get_profile()``, a redirect will be issued to the
:view:`profiles.views.edit_profile` view. If no profile model has been
specified in the ``AUTH_PROFILE_MODULE`` setting,
``django.contrib.auth.models.SiteProfileNotAvailable`` will be raised.

**Optional arguments:**

``extra_context``
    A dictionary of variables to add to the template context. Any
    callable object in this dictionary will be called to produce the
    end result which appears in the context.

``form_class``
    The form class to use for validating and creating the user
    profile. This form class must define a method named ``save()``,
    implementing the same argument signature as the ``save()`` method
    of a standard Django ``ModelForm`` (this view will call
    ``save(commit=False)`` to obtain the profile object, and fill in
    the user before the final save). If the profile object includes
    many-to-many relations, the convention established by
    ``ModelForm`` of using a method named ``save_m2m()`` will be used,
    and so your form class should also define this method.
    
    If this argument is not supplied, this view will use a
    ``ModelForm`` automatically generated from the model specified by
    ``AUTH_PROFILE_MODULE``.

``success_url``
    The URL to redirect to after successful profile creation. If this
    argument is not supplied, this will default to the URL of
    :view:`profiles.views.profile_detail` for the newly-created
    profile object.

``template_name``
    The template to use when displaying the profile-creation form. If
    not supplied, this will default to
    :template:`profiles/create_profile.html`.

**Context:**

``form``
    The profile-creation form.

**Template:**

``template_name`` keyword argument, or
:template:`profiles/create_profile.html`.


``profiles.views.edit_profile``
===============================

Edit the current user's profile.

If the user does not already have a profile (as determined by
``User.get_profile()``), a redirect will be issued to the
:view:`profiles.views.create_profile` view; if no profile model has
been specified in the ``AUTH_PROFILE_MODULE`` setting,
``django.contrib.auth.models.SiteProfileNotAvailable`` will be raised.

**Optional arguments:**

``extra_context``
    A dictionary of variables to add to the template context. Any
    callable object in this dictionary will be called to produce the
    end result which appears in the context.

``form_class``
    The form class to use for validating and editing the user
    profile. This form class must operate similarly to a standard
    Django ``ModelForm`` in that it must accept an instance of the
    object to be edited as the keyword argument ``instance`` to its
    constructor, and it must implement a method named ``save()`` which
    will save the updates to the object. If this argument is not
    specified, this view will use a ``ModelForm`` generated from the
    model specified in the ``AUTH_PROFILE_MODULE`` setting.

``success_url``
    The URL to redirect to following a successful edit. If not
    specified, this will default to the URL of
    :view:`profiles.views.profile_detail` for the profile object being
    edited.

``template_name``
    The template to use when displaying the profile-editing form. If
    not specified, this will default to
    :template:`profiles/edit_profile.html`.
    
**Context:**

``form``
    The form for editing the profile.
    
``profile``
     The user's current profile.

**Template:**

``template_name`` keyword argument or
:template:`profiles/edit_profile.html`.


``profiles.views.profile_detail``
=================================

Detail view of a user's profile.

If no profile model has been specified in the ``AUTH_PROFILE_MODULE``
setting, ``django.contrib.auth.models.SiteProfileNotAvailable`` will
be raised.
    
If the user has not yet created a profile, ``Http404`` will be raised.

**Required arguments:**

``username``
    The username of the user whose profile is being displayed.

**Optional arguments:**

``extra_context``
    A dictionary of variables to add to the template context. Any
    callable object in this dictionary will be called to produce the
    end result which appears in the context.

``public_profile_field``
    The name of a ``BooleanField`` on the profile model; if the value
    of that field on the user's profile is ``False``, the ``profile``
    variable in the template will be ``None``. Use this feature to
    allow users to mark their profiles as not being publicly viewable.
    
    If this argument is not specified, it will be assumed that all
    users' profiles are publicly viewable.
    
``template_name``
    The name of the template to use for displaying the profile. If not
    specified, this will default to
    :template:`profiles/profile_detail.html`.
    
**Context:**

``profile``
    The user's profile, or ``None`` if the user's profile is not
    publicly viewable (see the description of ``public_profile_field``
    above).
    
**Template:**

``template_name`` keyword argument or
:template:`profiles/profile_detail.html`.


``profiles.views.profile_list``
===============================

A list of user profiles.

If no profile model has been specified in the ``AUTH_PROFILE_MODULE``
setting, ``django.contrib.auth.models.SiteProfileNotAvailable`` will
be raised.

**Optional arguments:**

``public_profile_field``
    The name of a ``BooleanField`` on the profile model; if the value
    of that field on a user's profile is ``False``, that profile will
    be excluded from the list. Use this feature to allow users to mark
    their profiles as not being publicly viewable.
    
    If this argument is not specified, it will be assumed that all
    users' profiles are publicly viewable.

``template_name``
    The name of the template to use for displaying the profiles. If
    not specified, this will default to
    :template:`profiles/profile_list.html`.

Additionally, all arguments accepted by the
:view:`django.views.generic.list_detail.object_list` generic view will
be accepted here, and applied in the same fashion, with one exception:
``queryset`` will always be the ``QuerySet`` of the model specified by
the ``AUTH_PROFILE_MODULE`` setting, optionally filtered to remove
non-publicly-viewable proiles.

**Context:**

Same as the :view:`django.views.generic.list_detail.object_list`
generic view.

**Template:**

``template_name`` keyword argument or
:template:`profiles/profile_list.html`.
