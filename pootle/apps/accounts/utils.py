# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools
import logging
import sys

from django.contrib.auth import get_user_model
from django.core.validators import ValidationError, validate_email
from django.db.models import Count

from allauth.account.models import EmailAddress
from allauth.account.utils import sync_user_email_addresses

from pootle.core.contextmanagers import keep_data
from pootle.core.models import Revision
from pootle.core.signals import update_data
from pootle_store.constants import FUZZY, UNTRANSLATED
from pootle_store.util import SuggestionStates


logger = logging.getLogger(__name__)


def get_user_by_email(email):
    """Retrieves auser by its email address.

    First it looks up the `EmailAddress` entries, and as a safety measure
    falls back to looking up the `User` entries (these addresses are
    sync'ed in theory).

    :param email: address of the user to look up.
    :return: `User` instance belonging to `email`, `None` otherwise.
    """
    try:
        return EmailAddress.objects.get(email__iexact=email).user
    except EmailAddress.DoesNotExist:
        try:
            User = get_user_model()
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None


def write_stdout(start_msg, end_msg="DONE\n", fail_msg="FAILED\n"):

    def class_wrapper(f):

        @functools.wraps(f)
        def method_wrapper(self, *args, **kwargs):
            sys.stdout.write(start_msg % self.__dict__)
            try:
                result = f(self, *args, **kwargs)
            except Exception as e:
                sys.stdout.write(fail_msg % self.__dict__)
                logger.exception(e)
                raise e
            sys.stdout.write(end_msg % self.__dict__)
            return result
        return method_wrapper
    return class_wrapper


class UserMerger(object):

    def __init__(self, src_user, target_user):
        """Purges src_user from site reverting any changes that they have made.

        :param src_user: `User` instance to merge from.
        :param target_user: `User` instance to merge to.
        """
        self.src_user = src_user
        self.target_user = target_user

    @write_stdout("Merging user: "
                  "%(src_user)s --> %(target_user)s...\n",
                  "User merged: %(src_user)s --> %(target_user)s \n")
    def merge(self):
        """Merges one user to another.

        The following are fields are updated (model: fields):
        - units: submitted_by, commented_by, reviewed_by
        - submissions: submitter
        - suggestions: user, reviewer
        """
        self.merge_submitted()
        self.merge_commented()
        self.merge_reviewed()
        self.merge_submissions()
        self.merge_suggestions()
        self.merge_reviews()

    @write_stdout(" * Merging units comments: "
                  "%(src_user)s --> %(target_user)s... ")
    def merge_commented(self):
        """Merge commented_by attribute on units
        """
        self.src_user.units_commented.update(commented_by=self.target_user)

    @write_stdout(" * Merging units reviewed: "
                  "%(src_user)s --> %(target_user)s... ")
    def merge_reviewed(self):
        """Merge reviewed_by attribute on units
        """
        self.src_user.units_reviewed.update(reviewed_by=self.target_user)

    @write_stdout(" * Merging suggestion reviews: "
                  "%(src_user)s --> %(target_user)s... ")
    def merge_reviews(self):
        """Merge reviewer attribute on suggestions
        """
        self.src_user.reviews.update(reviewer=self.target_user)

    @write_stdout(" * Merging remaining submissions: "
                  "%(src_user)s --> %(target_user)s... ")
    def merge_submissions(self):
        """Merge submitter attribute on submissions
        """
        # Delete orphaned submissions.
        self.src_user.submission_set.filter(unit__isnull=True).delete()

        # Before we can save we first have to remove existing score_logs for
        # src_user - they will be recreated on save for target_user
        self.src_user.scorelog_set.all().delete()

        # Update submitter on submissions
        self.src_user.submission_set.update(submitter=self.target_user)

    @write_stdout(" * Merging units submitted_by: "
                  "%(src_user)s --> %(target_user)s... ")
    def merge_submitted(self):
        """Merge submitted_by attribute on units
        """
        self.src_user.units_submitted.update(submitted_by=self.target_user)

    @write_stdout(" * Merging suggestions: "
                  "%(src_user)s --> %(target_user)s... ")
    def merge_suggestions(self):
        """Merge user attribute on suggestions
        """
        # Update user and reviewer on suggestions
        self.src_user.suggestions.update(user=self.target_user)


class UserPurger(object):

    def __init__(self, user):
        """Purges user from site reverting any changes that they have made.

        :param user: `User` to purge.
        """
        self.user = user

    @write_stdout("Purging user: %(user)s... \n", "User purged: %(user)s \n")
    def purge(self):
        """Purges user from site reverting any changes that they have made.

        The following steps are taken:
        - Delete units created by user and without other submissions.
        - Revert units edited by user.
        - Revert reviews made by user.
        - Revert unit comments by user.
        - Revert unit state changes by user.
        - Delete any remaining submissions and suggestions.
        """

        stores = set()
        with keep_data():
            stores |= self.remove_units_created()
            stores |= self.revert_units_edited()
            stores |= self.revert_units_reviewed()
            stores |= self.revert_units_commented()
            stores |= self.revert_units_state_changed()

            # Delete remaining submissions.
            logger.debug("Deleting remaining submissions for: %s", self.user)
            self.user.submission_set.all().delete()

            # Delete remaining suggestions.
            logger.debug("Deleting remaining suggestions for: %s", self.user)
            self.user.suggestions.all().delete()
        for store in stores:
            update_data.send(store.__class__, instance=store)

    @write_stdout(" * Removing units created by: %(user)s... ")
    def remove_units_created(self):
        """Remove units created by user that have not had further
        activity.
        """

        stores = set()
        # Delete units created by user without submissions by others.
        for unit in self.user.get_units_created().iterator():
            stores.add(unit.store)
            # Find submissions by other users on this unit.
            other_subs = unit.submission_set.exclude(submitter=self.user)

            if not other_subs.exists():
                unit.delete()
                logger.debug("Unit deleted: %s", repr(unit))
        return stores

    @write_stdout(" * Reverting unit comments by: %(user)s... ")
    def revert_units_commented(self):
        """Revert comments made by user on units to previous comment or else
        just remove the comment.
        """
        stores = set()
        # Revert unit comments where self.user is latest commenter.
        for change in self.user.units_commented.iterator():
            unit = change.unit
            stores.add(unit.store)

            # Find comments by other self.users
            comments = unit.get_comments().exclude(submitter=self.user)

            if comments.exists():
                # If there are previous comments by others update the
                # translator_comment, commented_by, and commented_on
                last_comment = comments.latest('pk')
                unit.translator_comment = last_comment.new_value
                unit.change.commented_by_id = last_comment.submitter_id
                unit.change.commented_on = last_comment.creation_time
                logger.debug("Unit comment reverted: %s", repr(unit))
            else:
                unit.translator_comment = ""
                unit.change.commented_by = None
                unit.change.commented_on = None
                logger.debug("Unit comment removed: %s", repr(unit))

            # Increment revision
            unit.revision = Revision.incr()
            unit.save()
        return stores

    @write_stdout(" * Reverting units edited by: %(user)s... ")
    def revert_units_edited(self):
        """Revert unit edits made by a user to previous edit.
        """
        stores = set()
        # Revert unit target where user is the last submitter.
        for change in self.user.units_submitted.iterator():
            unit = change.unit
            stores.add(unit.store)

            # Find the last submission by different user that updated the
            # unit.target.
            edits = unit.get_edits().exclude(submitter=self.user)
            user = None
            submitted_on = None
            if edits.exists():
                last_edit = edits.order_by("-creation_time", "-pk").first()
                unit.target_f = last_edit.new_value
                user = last_edit.submitter
                unit.change.submitted_by_id = last_edit.submitter
                unit.change.submitted_on = last_edit.creation_time
                submitted_on = last_edit.creation_time
                logger.debug("Unit edit reverted: %s", repr(unit))
            else:
                # if there is no previous submissions set the target to "" and
                # set the unit.submitted_by to None
                unit.target_f = ""
                unit.change.submitted_by = None
                unit.change.submitted_on = unit.creation_time
                logger.debug("Unit edit removed: %s", repr(unit))

            # Increment revision
            unit.revision = Revision.incr()
            unit.save(user=user, submitted_on=submitted_on)
        return stores

    @write_stdout(" * Reverting units reviewed by: %(user)s... ")
    def revert_units_reviewed(self):
        """Revert reviews made by user on suggestions to previous state.
        """

        stores = set()
        # Revert reviews by this user.
        for review in self.user.get_suggestion_reviews().iterator():
            suggestion = review.suggestion
            stores.add(suggestion.unit.store)
            if suggestion.user_id == self.user.id:
                # If the suggestion was also created by this user then remove
                # both review and suggestion.
                suggestion.delete()
                logger.debug("Suggestion removed: %s", (suggestion))
            elif suggestion.reviewer_id == self.user.id:
                # If the suggestion is showing as reviewed by the user, then
                # set the suggestion back to pending and update
                # reviewer/review_time.
                suggestion.state = SuggestionStates.PENDING
                suggestion.reviewer = None
                suggestion.review_time = None
                suggestion.save()
                logger.debug("Suggestion reverted: %s", (suggestion))

            # Remove the review.
            review.delete()

        for change in self.user.units_reviewed.iterator():
            unit = change.unit
            stores.add(unit.store)
            reviews = unit.get_suggestion_reviews().exclude(
                submitter=self.user)
            if reviews.exists():
                previous_review = reviews.latest('pk')
                unit.change.reviewed_by_id = previous_review.submitter_id
                unit.change.reviewed_on = previous_review.creation_time
                logger.debug("Unit reviewed_by reverted: %s", repr(unit))
            else:
                unit.change.reviewed_by = None
                unit.change.reviewed_on = None

                # Increment revision
                unit.revision = Revision.incr()
                logger.debug("Unit reviewed_by removed: %s", repr(unit))
            unit.save()
        return stores

    @write_stdout(" * Reverting unit state changes by: %(user)s... ")
    def revert_units_state_changed(self):
        """Revert unit edits made by a user to previous edit.
        """
        stores = set()
        # Delete orphaned submissions.
        self.user.submission_set.filter(unit__isnull=True).delete()

        for submission in self.user.get_unit_states_changed().iterator():
            unit = submission.unit
            stores.add(unit.store)

            # We have to get latest by pk as on mysql precision is not to
            # microseconds - so creation_time can be ambiguous
            if submission != unit.get_state_changes().latest('pk'):
                # If the unit has been changed more recently we don't need to
                # revert the unit state.
                submission.delete()
                return
            submission.delete()
            other_submissions = (unit.get_state_changes()
                                     .exclude(submitter=self.user))
            if other_submissions.exists():
                new_state = other_submissions.latest('pk').new_value
            else:
                new_state = UNTRANSLATED
            if new_state != unit.state:
                if unit.state == FUZZY:
                    unit.markfuzzy(False)
                elif new_state == FUZZY:
                    unit.markfuzzy(True)
                unit.state = new_state

                # Increment revision
                unit.revision = Revision.incr()
                unit.save()
                logger.debug("Unit state reverted: %s", repr(unit))
        return stores


def verify_user(user):
    """Verify a user account without email confirmation

    If the user has an existing primary allauth.EmailAddress set then this is
    verified.

    Otherwise, an allauth.EmailAddress is created using email set for
    User.email.

    If the user is already verified raises a ValueError

    :param user: `User` to verify
    """
    if not user.email:
        raise ValidationError("You cannot verify an account with no email "
                              "set. You can set this user's email with "
                              "'pootle update_user_email %s EMAIL'"
                              % user.username)

    # Ensure this user's email address is unique
    try:
        validate_email_unique(user.email, user)
    except ValidationError:
        raise ValidationError("This user's email is not unique. You can find "
                              "duplicate emails with 'pootle "
                              "find_duplicate_emails'")

    # already has primary?
    existing_primary = EmailAddress.objects.filter(user=user, primary=True)
    if existing_primary.exists():
        existing_primary = existing_primary.first()
        if not existing_primary.verified:
            existing_primary.verified = True
            existing_primary.save()
            return
        else:
            # already verified
            raise ValueError("User '%s' is already verified" % user.username)

    sync_user_email_addresses(user)
    email_address = (EmailAddress.objects
                     .filter(user=user, email__iexact=user.email)
                     .order_by("primary")).first()
    email_address.verified = True
    email_address.primary = True
    email_address.save()


def get_duplicate_emails():
    """Get a list of emails that occur more than once in user accounts.
    """
    return (get_user_model().objects.hide_meta()
                                    .values('email')
                                    .annotate(Count('email'))
                                    .filter(email__count__gt=1)
                                    .values_list("email", flat=True))


def validate_email_unique(email, for_user=None):
    """Validates an email to ensure it does not already exist in the system.

    :param email: Email address to validate for uniqueness.
    :param for_user: Optionally check an email address is unique to this user
    """
    existing_accounts = get_user_model().objects.filter(email=email)
    existing_email = EmailAddress.objects.filter(email=email)
    if for_user is not None:
        existing_accounts = existing_accounts.exclude(pk=for_user.pk)
        existing_email = existing_email.exclude(user=for_user)

    if existing_accounts.exists() or existing_email.exists():
        raise ValidationError("A user with that email address already exists")


def update_user_email(user, new_email):
    """Updates a user's email with new_email.

    :param user: `User` to update email for.
    :param new_email: Email address to update with.
    """
    validate_email_unique(new_email)
    validate_email(new_email)
    user.email = new_email
    user.save()
