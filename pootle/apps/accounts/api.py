# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from django.contrib.auth import get_user_model

from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized

from pootle.core.api import StatisticsModelResource


User = get_user_model()


class UserObjectsOnlyAuthorization(DjangoAuthorization):
    """Custom Authorization class for checking access to UserResource objects.

    This relies on DjangoAuthorization provided by Tastypie, but ensures that:

    * User resources are only accessed if the consumer is the resource owner,
    * All consumers can access all users statistics.
    """
    def _get_authorized_objects(self, object_list, bundle):
        """Return the object list only with objects owned by the consumer.

        Return the complete object list if the consumer is a superuser.

        Should return an empty list if none are allowed.
        """
        # Do not show any object when performing a GET request unless an exact
        # filter on 'username' is provided.
        if (bundle.request.method == 'GET' and
            'username__exact' not in bundle.request.GET):
            raise Unauthorized("You are not allowed to access that resource.")

        # If the consumer is a superuser then return all the objects.
        if bundle.request.user.is_superuser:
            return object_list

        # This assumes that object_list is a QuerySet from ModelResource.
        return object_list.filter(pk=bundle.request.user.pk)

    def _is_authorized_for_object(self, bundle):
        """Return the authorization status for current object.

        This method:

        * Returns ``True`` if the object belongs to the consumer, or if the
          consumer is a superuser,
        * Raises ``Unauthorized`` if it doesn't belong to the consumer.
        """
        if (bundle.obj == bundle.request.user or
            bundle.request.user.is_superuser or
            bundle.request.path.endswith("/statistics/")):
            return True
        raise Unauthorized("You are not allowed to access that resource.")

    def read_list(self, object_list, bundle):
        """Return a list of all the objects the consumer is allowed to read.

        Should return an empty list if none are allowed.
        """
        object_list = super(UserObjectsOnlyAuthorization, self).read_list(
                object_list, bundle)
        return self._get_authorized_objects(object_list, bundle)

    def read_detail(self, object_list, bundle):
        """Return the authorization status for reading the current object.

        This method:

        * Returns ``True`` if the consumer is allowed to read the object,
        * Raises ``Unauthorized`` if the consumer is not allowed to read it.
        """
        authorized = super(UserObjectsOnlyAuthorization, self).read_detail(
                object_list, bundle)
        return authorized and self._is_authorized_for_object(bundle)

    def update_list(self, object_list, bundle):
        """Return a list of all the objects the consumer is allowed to update.

        Should return an empty list if none are allowed.
        """
        object_list = super(UserObjectsOnlyAuthorization, self).update_list(
                object_list, bundle)
        return self._get_authorized_objects(object_list, bundle)

    def update_detail(self, object_list, bundle):
        """Return the authorization status for updating the current object.

        This method:

        * Returns ``True`` if the consumer is allowed to update the object,
        * Raises ``Unauthorized`` if the consumer is not allowed to update it.
        """
        authorized = super(UserObjectsOnlyAuthorization, self).update_detail(
                object_list, bundle)
        return authorized and self._is_authorized_for_object(bundle)

    def delete_list(self, object_list, bundle):
        """Return a list of all the objects the consumer is allowed to delete.

        Should return an empty list if none are allowed.
        """
        object_list = super(UserObjectsOnlyAuthorization, self).delete_list(
                object_list, bundle)
        return self._get_authorized_objects(object_list, bundle)

    def delete_detail(self, object_list, bundle):
        """Return the authorization status for deleting the current object.

        This method:

        * Returns ``True`` if the consumer is allowed to delete the object,
        * Raises ``Unauthorized`` if the consumer is not allowed to delete it.
        """
        authorized = super(UserObjectsOnlyAuthorization, self).delete_detail(
                object_list, bundle)
        return authorized and self._is_authorized_for_object(bundle)


class UserResource(StatisticsModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'users'
        fields = [
            'date_joined',
            'email',
            'full_name',
            'username',
        ]
        list_allowed_methods = ['post', 'get']
        filtering = {
            "username": ('exact', ),
        }
        # List of fields shown when visiting /statistics/
        statistics_fields = [
            'statistics',
            'username',
        ]
        # HTTP methods allowed for visiting /statistics/ URLs.
        statistics_allowed_methods = ['get']
        authorization = UserObjectsOnlyAuthorization()
        authentication = BasicAuthentication()

    def obj_create(self, bundle, **kwargs):
        """Custom user creation that sends a password reset email."""
        value = super(UserResource, self).obj_create(bundle, **kwargs)

        # Send the password reset email so the user can set its own password.
        from django.contrib.auth.forms import PasswordResetForm
        from django.conf import settings

        form = PasswordResetForm({'email': bundle.obj.email})
        form.full_clean()
        tpl = "account/password_reset_email_for_api_user_creation.html"
        form.save(email_template_name=tpl,
                  from_email=settings.DEFAULT_FROM_EMAIL)

        return value

    def retrieve_statistics(self, bundle):
        """Retrieve the statistics for the current resource object."""
        up = User.objects.get(user=bundle.obj)
        return up.contributions

    def dehydrate(self, bundle):
        """A hook to allow final manipulation of data.

        It is run after all fields/methods have built out the dehydrated data.

        Useful if you need to access more than one dehydrated field or want to
        annotate on additional data.

        Must return the modified bundle.
        """
        bundle = super(UserResource, self).dehydrate(bundle)
        if not bundle.obj == bundle.request.user:
            # Remove sensitive data when other users look at the statistics for
            # a given user.
            for field in self._meta.fields:
                if field not in self._meta.statistics_fields:
                    bundle.data.pop(field, None)
        return bundle
