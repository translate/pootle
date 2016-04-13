# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from pytest_pootle.factories import (PaidTaskFactory, SubmissionFactory,
                                     ScoreLogFactory, UserFactory)

from pootle_statistics.models import (SubmissionFields, SubmissionTypes,
                                      TranslationActionCodes)
from reports.models.invoice import Invoice, MONTH_FORMAT, get_previous_month
from reports.models.paidtask import PaidTask, PaidTaskTypes


FAKE_CONFIG = {
    'name': 'Foo',
    'paid_by': 'Bar',
    'wire_info': 'Baz 01234',
}


FAKE_EMAIL_CONFIG = dict({
    'email': 'foo@example.org',
    'accounting_email': 'bar@example.com',
}, **FAKE_CONFIG)


@pytest.fixture()
def invoice_directory(settings, tmpdir):
    """Sets up a tmp invoices directory."""
    invoices_dir = tmpdir.mkdir('invoices')
    settings.POOTLE_INVOICES_DIRECTORY = str(invoices_dir)
    return invoices_dir


@pytest.mark.parametrize('month', [
    None, timezone.now(), timezone.datetime(2014, 04, 01),
])
def test_invoice_repr(month):
    user = UserFactory.build()
    format_month = get_previous_month() if month is None else month
    assert (
        repr(Invoice(user, FAKE_CONFIG, month=month)) == u'<Invoice %s:%s>'
        % (user.username, format_month.strftime(MONTH_FORMAT))
    )


@pytest.mark.parametrize('config', [
    {},
    {
        'foo': None,
        'bar': False,
    },
    {
        'name': None,
        'paid_by': None,
    },
])
def test_invoice_init_incomplete_config(config):
    user = UserFactory.build()
    with pytest.raises(ImproperlyConfigured):
        Invoice(user, config)


@pytest.mark.django_db
def test_invoice_get_rates_inconsistent_scorelog_rates(member):
    USER_RATE_ONE = 0.5
    USER_RATE_TWO = 0.2

    # Set some rate
    member.rate = USER_RATE_ONE
    member.review_rate = USER_RATE_ONE
    member.save()

    from pootle_store.models import Store
    store = Store.objects.first()
    month = timezone.datetime(2014, 04, 01)

    submission_kwargs = {
        'store': store,
        'unit': store.units[0],
        'field': SubmissionFields.TARGET,
        'type': SubmissionTypes.NORMAL,
        'old_value': 'foo',
        'new_value': 'bar',
        'submitter': member,
        'translation_project': store.translation_project,
        'creation_time': month,
    }
    scorelog_kwargs = {
        'wordcount': 1,
        'similarity': 0,
        'action_code': TranslationActionCodes.NEW,
        'creation_time': month,
        'user': member,
        'submission': SubmissionFactory(**submission_kwargs),
    }

    ScoreLogFactory(**scorelog_kwargs)

    # Alter rates, producing an inconsistent state when recording the ScoreLog
    member.rate = USER_RATE_TWO
    member.review_rate = USER_RATE_TWO
    member.save()

    submission_kwargs['unit'] = store.units[1]
    scorelog_kwargs['submission'] = SubmissionFactory(**submission_kwargs)

    ScoreLogFactory(**scorelog_kwargs)
    invoice = Invoice(member, FAKE_CONFIG, month=month)

    with pytest.raises(ValueError) as e:
        invoice.get_rates()

    assert (
        'Multiple rate values recorded for user %s' % (member.username, )
        in e.value.message
    )


@pytest.mark.django_db
@pytest.mark.parametrize('task_type, task_type_name, user_rate_attr_name', [
    (PaidTaskTypes.TRANSLATION, 'TRANSLATION', 'rate'),
    (PaidTaskTypes.REVIEW, 'REVIEW', 'review_rate'),
])
def test_invoice_get_rates_inconsistent_paidtask_rates(member, task_type,
                                                       task_type_name,
                                                       user_rate_attr_name):
    USER_RATE = 0.5
    PAID_TASK_RATE = 0.2

    # Set some user rate
    setattr(member, user_rate_attr_name, USER_RATE)
    member.save()

    from pootle_store.models import Store
    store = Store.objects.first()
    month = timezone.datetime(2014, 04, 01)

    submission_kwargs = {
        'store': store,
        'unit': store.units[0],
        'field': SubmissionFields.TARGET,
        'type': SubmissionTypes.NORMAL,
        'old_value': 'foo',
        'new_value': 'bar',
        'submitter': member,
        'translation_project': store.translation_project,
        'creation_time': month,
    }
    scorelog_kwargs = {
        'wordcount': 1,
        'similarity': 0,
        'action_code': TranslationActionCodes.NEW,
        'creation_time': month,
        'user': member,
        'submission': SubmissionFactory(**submission_kwargs),
    }
    paid_task_kwargs = {
        'rate': PAID_TASK_RATE,  # Note how this doesn't match user's rate
        'datetime': month,
        'user': member,
        'task_type': task_type,
    }

    ScoreLogFactory(**scorelog_kwargs)
    PaidTaskFactory(**paid_task_kwargs)
    invoice = Invoice(member, FAKE_CONFIG, month=month)

    with pytest.raises(ValueError) as e:
        invoice.get_rates()

    assert (
        'Multiple %s rate values for user %s' % (task_type_name,
                                                 member.username)
        in e.value.message
    )


@pytest.mark.django_db
def test_invoice_get_rates_inconsistent_hourly_paidtask_rates(member):
    PAID_TASK_RATE_ONE = 0.5
    PAID_TASK_RATE_TWO = 0.2

    month = timezone.datetime(2014, 04, 01)

    paid_task_kwargs = {
        'rate': PAID_TASK_RATE_ONE,  # Note how this doesn't match user's rate
        'datetime': month,
        'user': member,
        'task_type': PaidTaskTypes.HOURLY_WORK,
    }

    PaidTaskFactory(**paid_task_kwargs)
    PaidTaskFactory(**dict(paid_task_kwargs, rate=PAID_TASK_RATE_TWO))
    invoice = Invoice(member, FAKE_CONFIG, month=month)

    with pytest.raises(ValueError) as e:
        invoice.get_rates()

    assert (
        'Multiple HOURLY_WORK rate values for user %s' % (member.username)
        in e.value.message
    )


@pytest.mark.django_db
@pytest.mark.parametrize('task_type, task_type_name, user_rate_attr_name', [
    (PaidTaskTypes.TRANSLATION, 'TRANSLATION', 'rate'),
    (PaidTaskTypes.REVIEW, 'REVIEW', 'review_rate'),
])
def test_invoice_get_rates_scorelog_rates(member, task_type, task_type_name,
                                          user_rate_attr_name):
    """Tests that `Invoice.get_rates()` returns the rates set for users in their
    `ScoreLog` entries.
    """
    USER_RATE_ONE = 0.5
    USER_RATE_TWO = 0.2

    # Set some user rate
    setattr(member, user_rate_attr_name, USER_RATE_ONE)
    member.save()

    from pootle_store.models import Store
    store = Store.objects.first()
    month = timezone.datetime(2014, 04, 01)

    submission_kwargs = {
        'store': store,
        'unit': store.units[0],
        'field': SubmissionFields.TARGET,
        'type': SubmissionTypes.NORMAL,
        'old_value': 'foo',
        'new_value': 'bar',
        'submitter': member,
        'translation_project': store.translation_project,
        'creation_time': month,
    }
    scorelog_kwargs = {
        'wordcount': 1,
        'similarity': 0,
        'action_code': TranslationActionCodes.NEW,
        'creation_time': month,
        'user': member,
        'submission': SubmissionFactory(**submission_kwargs),
    }

    ScoreLogFactory(**scorelog_kwargs)
    invoice = Invoice(member, FAKE_CONFIG, month=month)

    # Set user rate to something else to ensure we get the recorded rates
    setattr(member, user_rate_attr_name, USER_RATE_TWO)
    member.save()

    rate, review_rate, hourly_rate = invoice.get_rates()
    assert locals()[user_rate_attr_name] == USER_RATE_ONE


@pytest.mark.django_db
def test_invoice_get_rates_paidtask_rates(member):
    """Tests that `Invoice.get_rates()` returns the rates set for users in their
    `PaidTask` entries.
    """
    USER_RATE_ONE = 0.5
    USER_RATE_TWO = 0.2

    # Set some user rate
    member.hourly_rate = USER_RATE_ONE
    member.save()

    month = timezone.datetime(2014, 04, 01)

    paid_task_kwargs = {
        'rate': USER_RATE_ONE,
        'datetime': month,
        'user': member,
        'task_type': PaidTaskTypes.HOURLY_WORK,
    }
    PaidTaskFactory(**paid_task_kwargs)

    invoice = Invoice(member, FAKE_CONFIG, month=month)

    # Set user rate to something else to ensure we get the recorded rates
    member.hourly_rate = USER_RATE_TWO
    member.save()

    rate, review_rate, hourly_rate = invoice.get_rates()
    assert hourly_rate == USER_RATE_ONE


@pytest.mark.django_db
def test_invoice_get_rates_user(member):
    """Tests that `Invoice.get_rates()` returns the rates set for users in their
    user model.
    """
    USER_RATE = 0.5

    # Set some user rate
    member.rate = USER_RATE
    member.review_rate = USER_RATE
    member.hourly_rate = USER_RATE
    member.save()

    month = timezone.datetime(2014, 04, 01)
    invoice = Invoice(member, FAKE_CONFIG, month=month)

    rate, review_rate, hourly_rate = invoice.get_rates()
    assert rate == USER_RATE
    assert review_rate == USER_RATE
    assert hourly_rate == USER_RATE


@pytest.mark.django_db
@pytest.mark.parametrize('task_type', (PaidTaskTypes.TRANSLATION,
                                       PaidTaskTypes.REVIEW,
                                       PaidTaskTypes.HOURLY_WORK,
                                       PaidTaskTypes.CORRECTION))
@pytest.mark.parametrize('action_code', (TranslationActionCodes.NEW,
                                         TranslationActionCodes.REVIEWED))
def test_invoice_get_user_amounts(member, action_code, task_type):
    """Tests that `Invoice._get_user_amounts()` returns the total amount of work
    performed for the given user when their activities were recorded via both
    score logs and paid tasks.
    """
    from pootle_store.models import Store
    EVENT_COUNT = 5
    WORDCOUNT = 5
    TASK_COUNT = 5
    PAID_TASK_AMOUNT = 22
    month = timezone.datetime(2014, 04, 01)

    submission_kwargs = {
        'field': SubmissionFields.TARGET,
        'type': SubmissionTypes.NORMAL,
        'old_value': 'foo',
        'new_value': 'bar',
        'submitter': member,
        'creation_time': month,
    }
    for i in range(EVENT_COUNT):
        store = Store.objects.all()[i]
        submission_kwargs.update({
            'store': store,
            'unit': store.units[0],
            'translation_project': store.translation_project,
        })
        scorelog_kwargs = {
            'wordcount': WORDCOUNT,
            'similarity': 0,
            'action_code': action_code,
            'creation_time': month,
            'user': member,
            'submission': SubmissionFactory(**submission_kwargs),
        }
        ScoreLogFactory(**scorelog_kwargs)

    for i in range(TASK_COUNT):
        paid_task_kwargs = {
            'amount': PAID_TASK_AMOUNT,
            'datetime': month,
            'user': member,
            'task_type': task_type,
        }
        PaidTaskFactory(**paid_task_kwargs)

    invoice = Invoice(member, FAKE_CONFIG, month=month)

    translated, reviewed, hours, correction = invoice._get_user_amounts(member)

    if (action_code == TranslationActionCodes.NEW and
        task_type == PaidTaskTypes.TRANSLATION):
        assert translated == (EVENT_COUNT * WORDCOUNT +
                              TASK_COUNT * PAID_TASK_AMOUNT)
    elif action_code == TranslationActionCodes.NEW:
        assert translated == EVENT_COUNT * WORDCOUNT
    elif task_type == PaidTaskTypes.TRANSLATION:
        assert translated == TASK_COUNT * PAID_TASK_AMOUNT
    else:
        assert translated == 0

    if (action_code == TranslationActionCodes.REVIEWED and
        task_type == PaidTaskTypes.REVIEW):
        assert reviewed == (EVENT_COUNT * WORDCOUNT +
                            TASK_COUNT * PAID_TASK_AMOUNT)
    elif action_code == TranslationActionCodes.REVIEWED:
        assert reviewed == EVENT_COUNT * WORDCOUNT
    elif task_type == PaidTaskTypes.REVIEW:
        assert reviewed == TASK_COUNT * PAID_TASK_AMOUNT
    else:
        assert reviewed == 0

    if task_type == PaidTaskTypes.HOURLY_WORK:
        assert hours == TASK_COUNT * PAID_TASK_AMOUNT
    else:
        assert hours == 0

    if task_type == PaidTaskTypes.CORRECTION:
        assert correction == TASK_COUNT * PAID_TASK_AMOUNT
    else:
        assert correction == 0


def test_invoice_get_total_amounts_below_minimal_payment(monkeypatch):
    """Tests total amounts' correctness when the accrued total is below the
    minimal payment bar.
    """
    user = UserFactory.build()
    config = dict({
        'minimal_payment': 10,
        'extra_add': 5,
    }, **FAKE_CONFIG)
    invoice = Invoice(user, config, add_correction=True)

    rates = (0.5, 0.5, 0.5)
    monkeypatch.setattr(invoice, 'get_rates', lambda: rates)
    amounts = (5, 5, 5, 0)
    monkeypatch.setattr(invoice, '_get_full_user_amounts', lambda x: amounts)

    total_amounts = invoice.get_total_amounts()
    assert total_amounts['subtotal'] == 3 * (amounts[0] * rates[0])
    assert total_amounts['balance'] == 3 * (amounts[0] * rates[0])
    assert total_amounts['total'] == 0
    assert total_amounts['extra_amount'] == 0


def test_invoice_get_total_amounts_extra_add(monkeypatch):
    """Tests total amounts' correctness when there is an extra amount to be
    added to the accrued total.
    """
    extra_add = 5
    user = UserFactory.build()
    config = dict({
        'extra_add': extra_add,
    }, **FAKE_CONFIG)
    invoice = Invoice(user, config, add_correction=True)

    rates = (0.5, 0.5, 0.5)
    monkeypatch.setattr(invoice, 'get_rates', lambda: rates)
    amounts = (5, 5, 5, 0)
    monkeypatch.setattr(invoice, '_get_full_user_amounts', lambda x: amounts)

    total_amounts = invoice.get_total_amounts()
    assert total_amounts['subtotal'] == 3 * (amounts[0] * rates[0])
    assert total_amounts['balance'] is None
    assert total_amounts['total'] == 3 * (amounts[0] * rates[0]) + extra_add
    assert total_amounts['extra_amount'] == extra_add


def _check_single_paidtask(invoice, amount):
    current_month_start = invoice.now.replace(
        day=1, hour=0, minute=0, second=0,
        tzinfo=timezone.get_default_timezone()
    )
    PaidTask.objects.get(
        task_type=PaidTaskTypes.CORRECTION,
        amount=(-1) * amount,
        datetime=invoice.month_end,
        description='Carryover to the next month',
        user=invoice.user,
    )
    PaidTask.objects.get(
        task_type=PaidTaskTypes.CORRECTION,
        amount=amount,
        datetime=current_month_start,
        description='Carryover from the previous month',
        user=invoice.user,
    )
    assert PaidTask.objects.filter(task_type=PaidTaskTypes.CORRECTION).count() == 2


@pytest.mark.django_db
def test_invoice_generate_add_correction(member, invoice_directory):
    """Tests that generating invoices multiple times for the same month + user
    will add corrections only once.
    """
    from pootle_store.models import Store
    EVENT_COUNT = 5
    WORDCOUNT = 5
    TRANSLATION_RATE = 0.5
    INITIAL_SUBTOTAL = EVENT_COUNT * WORDCOUNT * TRANSLATION_RATE
    MINIMAL_PAYMENT = 20

    month = get_previous_month()
    config = dict({
        'minimal_payment': MINIMAL_PAYMENT,
    }, **FAKE_CONFIG)
    invoice = Invoice(member, config, month=month, add_correction=True)

    # Set some rates
    member.rate = TRANSLATION_RATE
    member.save()

    # Fake some activity that will leave amounts below the minimum bar:
    # EVENT_COUNT * WORDCOUNT * TRANSLATION_RATE < MINIMAL_PAYMENT
    submission_kwargs = {
        'field': SubmissionFields.TARGET,
        'type': SubmissionTypes.NORMAL,
        'old_value': 'foo',
        'new_value': 'bar',
        'submitter': member,
        'creation_time': month,
    }
    for i in range(EVENT_COUNT):
        store = Store.objects.all()[i]
        submission_kwargs.update({
            'store': store,
            'unit': store.units[0],
            'translation_project': store.translation_project,
        })
        scorelog_kwargs = {
            'wordcount': WORDCOUNT,
            'similarity': 0,
            'action_code': TranslationActionCodes.NEW,
            'creation_time': month,
            'user': member,
            'submission': SubmissionFactory(**submission_kwargs),
        }
        ScoreLogFactory(**scorelog_kwargs)

    # Generate an invoice first
    amounts = invoice.get_total_amounts()
    assert amounts['subtotal'] == INITIAL_SUBTOTAL
    assert invoice.should_add_correction(amounts['subtotal'])
    invoice.generate()
    _check_single_paidtask(invoice, INITIAL_SUBTOTAL)

    # Subsequent invoice generations must not add any corrections
    for i in range(5):
        invoice.get_total_amounts.cache_clear()
        amounts = invoice.get_total_amounts()
        assert amounts['subtotal'] == 0
        assert not invoice.should_add_correction(amounts['subtotal'])
        invoice.generate()
        _check_single_paidtask(invoice, INITIAL_SUBTOTAL)
