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
from pootle.core.delegate import score_updater
from pootle.core.models import Revision
from pootle.core.signals import update_data, update_revisions
from pootle_app.models import Directory
from pootle_statistics.models import SubmissionFields
from pootle_store.constants import FUZZY, UNTRANSLATED
from pootle_store.models import SuggestionState


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
        # TODO: this need to update unitchange not unit
        self.src_user.commented.update(commented_by=self.target_user)

    @write_stdout(" * Merging units reviewed: "
                  "%(src_user)s --> %(target_user)s... ")
    def merge_reviewed(self):
        """Merge reviewed_by attribute on units
        """
        self.src_user.reviewed.update(reviewed_by=self.target_user)

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

        score_updater.get(
            self.src_user.__class__)(users=[self.src_user.id]).clear()

        # Update submitter on submissions
        self.src_user.submission_set.update(submitter=self.target_user)

    @write_stdout(" * Merging units submitted_by: "
                  "%(src_user)s --> %(target_user)s... ")
    def merge_submitted(self):
        """Merge submitted_by attribute on units
        """
        self.src_user.submitted.update(submitted_by=self.target_user)

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
        - Expire caches for relevant directories
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
        update_revisions.send(
            Directory,
            object_list=Directory.objects.filter(
                id__in=set(store.parent.id for store in stores)))

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
        for unit_change in self.user.commented.select_related("unit").iterator():
            unit = unit_change.unit
            stores.add(unit.store)

            # Find comments by other self.users
            comments = unit.get_comments().exclude(submitter=self.user)
            change = {}
            if comments.exists():
                # If there are previous comments by others update the
                # translator_comment, commented_by, and commented_on
                last_comment = comments.latest('pk')
                translator_comment = last_comment.new_value
                change["commented_by_id"] = last_comment.submitter_id
                change["commented_on"] = last_comment.creation_time
                logger.debug("Unit comment reverted: %s", repr(unit))
            else:
                translator_comment = ""
                change["commented_by"] = None
                change["commented_on"] = None
                logger.debug("Unit comment removed: %s", repr(unit))
            unit_change.__class__.objects.filter(id=unit_change.id).update(
                **change)
            unit.__class__.objects.filter(id=unit.id).update(
                translator_comment=translator_comment,
                revision=Revision.incr())
        return stores

    @write_stdout(" * Reverting units edited by: %(user)s... ")
    def revert_units_edited(self):
        """Revert unit edits made by a user to previous edit.
        """
        stores = set()
        # Revert unit target where user is the last submitter.
        for unit_change in self.user.submitted.select_related("unit").iterator():
            unit = unit_change.unit
            stores.add(unit.store)

            # Find the last submission by different user that updated the
            # unit.target.
            edits = unit.get_edits().exclude(submitter=self.user)
            updates = {}
            unit_updates = {}
            if edits.exists():
                last_edit = edits.latest("pk")
                unit_updates["target_f"] = last_edit.new_value
                updates["submitted_by_id"] = last_edit.submitter_id
                updates["submitted_on"] = last_edit.creation_time
                logger.debug("Unit edit reverted: %s", repr(unit))
            else:
                # if there is no previous submissions set the target to "" and
                # set the unit.change.submitted_by to None
                unit_updates["target_f"] = ""
                updates["submitted_by"] = None
                updates["submitted_on"] = unit.creation_time
                logger.debug("Unit edit removed: %s", repr(unit))

            # Increment revision
            unit_change.__class__.objects.filter(id=unit_change.id).update(
                **updates)
            unit.__class__.objects.filter(id=unit.id).update(
                revision=Revision.incr(),
                **unit_updates)
        return stores

    @write_stdout(" * Reverting units reviewed by: %(user)s... ")
    def revert_units_reviewed(self):
        """Revert reviews made by user on suggestions to previous state.
        """

        stores = set()
        pending = SuggestionState.objects.get(name="pending")

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
                suggestion.state = pending
                suggestion.reviewer = None
                suggestion.review_time = None
                suggestion.save()
                logger.debug("Suggestion reverted: %s", (suggestion))

            # Remove the review.
            review.delete()

        for unit_change in self.user.reviewed.select_related("unit").iterator():
            unit = unit_change.unit
            stores.add(unit.store)
            unit.suggestion_set.filter(reviewer=self.user).update(
                state=SuggestionState.objects.get(name="pending"),
                reviewer=None)
            unit_updates = {}
            updates = {}
            if not unit.target:
                unit_updates["state"] = UNTRANSLATED
                updates["reviewed_by"] = None
                updates["reviewed_on"] = None
            else:
                old_state_sub = unit.submission_set.exclude(
                    submitter=self.user).filter(
                        field=SubmissionFields.STATE).order_by(
                            "-creation_time", "-pk").first()
                if old_state_sub:
                    unit_updates["state"] = old_state_sub.new_value
                    updates["reviewed_by"] = old_state_sub.submitter
                    updates["reviewed_on"] = old_state_sub.creation_time
            logger.debug("Unit reviewed_by removed: %s", repr(unit))
            unit_change.__class__.objects.filter(id=unit_change.id).update(
                **updates)
            # Increment revision
            unit.__class__.objects.filter(id=unit.id).update(
                revision=Revision.incr(),
                **unit_updates)
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
                unit.__class__.objects.filter(id=unit.id).update(
                    revision=Revision.incr())
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
