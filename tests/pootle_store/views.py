import pytest

from pootle.core.debug import memusage
from pootle_store.constants import UNTRANSLATED


@pytest.mark.pootle_memusage
@pytest.mark.django_db
def test_submit_unit_memusage(client, store0, admin, settings, system):
    settings.POOTLE_CAPTCHA_ENABLED = False
    user = admin
    unit = store0.units.filter(state=UNTRANSLATED).first()
    if user.username != "nobody":
        client.login(
            username=user.username,
            password="admin")
    url = '/xhr/units/%d/' % unit.id
    response = client.post(
        url,
        dict(target_f_0=("%s changed" % unit.target),
             is_fuzzy="0",
             sfn="PTL.editor.processSubmission"),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    for i in xrange(0, 2):
        with memusage() as usage:
            client.post(
                url,
                dict(target_f_0=("%s changed" % unit.target),
                     is_fuzzy="0",
                     sfn="PTL.editor.processSubmission"),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert not usage["used"]


@pytest.mark.pootle_memusage
@pytest.mark.django_db
def test_get_units_memusage(client, tp0, request_users, settings, system):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    url = (
        '/xhr/units/?path=/%s/%s/'
        % (tp0.language.code, tp0.project.code))
    response = client.get(
        url,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    for i in xrange(0, 2):
        with memusage() as usage:
            client.get(
                url,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert not usage["used"]


@pytest.mark.pootle_memusage
@pytest.mark.django_db
def test_get_edit_unit_memusage(client, store0, request_users, settings, system):
    user = request_users["user"]
    unit = store0.units.filter(state=UNTRANSLATED).first()
    client.login(
        username=user.username,
        password=request_users["password"])
    url = (
        '/xhr/units/%s/edit' % unit.id)
    response = client.get(
        url,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    for i in xrange(0, 2):
        with memusage() as usage:
            client.get(
                url,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert not usage["used"]
