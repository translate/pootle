import time
import types

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import simplejson

from translate.storage import factory
from translate.storage import statsdb

from pootle.tests import PootleTestCase
from pootle_profile.models import get_profile
from pootle_store.models import Store

class UnitTests(PootleTestCase):
    def setUp(self):
        super(UnitTests, self).setUp()
        self.store = Store.objects.get(pootle_path="/af/tutorial/pootle.po")

    def _update_translation(self, item, newvalues):
        unit = self.store.getitem(item)
        time.sleep(1)
        if 'target' in newvalues:
            unit.target = newvalues['target']
        if 'fuzzy' in newvalues:
            unit.markfuzzy(newvalues['fuzzy'])
        if 'translator_comment' in newvalues:
            unit.translator_comment = newvalues['translator_comment']
        unit.save()
        self.store.sync(update_translation=True)
        return self.store.getitem(item)

    def test_getorig(self):
        for dbunit in self.store.units.iterator():
            storeunit = dbunit.getorig()
            self.assertEqual(dbunit.getid(), storeunit.getid())

    def test_convert(self):
        for dbunit in self.store.units.iterator():
            if dbunit.hasplural() and not dbunit.istranslated():
                # skip untranslated plural units, they will always look different
                continue
            storeunit = dbunit.getorig()
            newunit = dbunit.convert(self.store.file.store.UnitClass)
            self.assertEqual(str(newunit), str(storeunit))

    def test_update_target(self):
        dbunit = self._update_translation(0, {'target': u'samaka'})
        storeunit = dbunit.getorig()

        self.assertEqual(dbunit.target, u'samaka')
        self.assertEqual(dbunit.target, storeunit.target)
        pofile = factory.getobject(self.store.file.path)
        self.assertEqual(dbunit.target, pofile.units[dbunit.index].target)

    def test_update_plural_target(self):
        dbunit = self._update_translation(2, {'target': [u'samaka', u'samak']})
        storeunit = dbunit.getorig()

        self.assertEqual(dbunit.target.strings, [u'samaka', u'samak'])
        self.assertEqual(dbunit.target.strings, storeunit.target.strings)
        pofile = factory.getobject(self.store.file.path)
        self.assertEqual(dbunit.target.strings, pofile.units[dbunit.index].target.strings)

        self.assertEqual(dbunit.target, u'samaka')
        self.assertEqual(dbunit.target, storeunit.target)
        self.assertEqual(dbunit.target, pofile.units[dbunit.index].target)

    def test_update_plural_target_dict(self):
        dbunit = self._update_translation(2, {'target': {0: u'samaka', 1: u'samak'}})
        storeunit = dbunit.getorig()

        self.assertEqual(dbunit.target.strings, [u'samaka', u'samak'])
        self.assertEqual(dbunit.target.strings, storeunit.target.strings)
        pofile = factory.getobject(self.store.file.path)
        self.assertEqual(dbunit.target.strings, pofile.units[dbunit.index].target.strings)

        self.assertEqual(dbunit.target, u'samaka')
        self.assertEqual(dbunit.target, storeunit.target)
        self.assertEqual(dbunit.target, pofile.units[dbunit.index].target)

    def test_update_fuzzy(self):
        dbunit = self._update_translation(0, {'fuzzy': True})
        storeunit = dbunit.getorig()

        self.assertTrue(dbunit.isfuzzy())
        self.assertEqual(dbunit.isfuzzy(), storeunit.isfuzzy())
        pofile = factory.getobject(self.store.file.path)
        self.assertEqual(dbunit.isfuzzy(), pofile.units[dbunit.index].isfuzzy())

        time.sleep(1)

        dbunit = self._update_translation(0, {'fuzzy': False})
        storeunit = dbunit.getorig()

        self.assertFalse(dbunit.isfuzzy())
        self.assertEqual(dbunit.isfuzzy(), storeunit.isfuzzy())
        pofile = factory.getobject(self.store.file.path)
        self.assertEqual(dbunit.isfuzzy(), pofile.units[dbunit.index].isfuzzy())

    def test_update_comment(self):
        dbunit = self._update_translation(0, {'translator_comment': u'7amada'})
        storeunit = dbunit.getorig()

        self.assertEqual(dbunit.getnotes(origin="translator"), u'7amada')
        self.assertEqual(dbunit.getnotes(origin="translator"), storeunit.getnotes(origin="translator"))
        pofile = factory.getobject(self.store.file.path)
        self.assertEqual(dbunit.getnotes(origin="translator"), pofile.units[dbunit.index].getnotes(origin="translator"))


class StoreTests(PootleTestCase):
    def setUp(self):
        super(StoreTests, self).setUp()
        self.store = Store.objects.get(pootle_path="/af/tutorial/pootle.po")

    def test_quickstats(self):
        statscache = statsdb.StatsCache()
        dbstats = self.store.getquickstats()
        filestats = statscache.filetotals(self.store.file.path)

        self.assertEqual(dbstats['total'], filestats['total'])
        self.assertEqual(dbstats['totalsourcewords'], filestats['totalsourcewords'])
        self.assertEqual(dbstats['untranslated'], filestats['untranslated'])
        self.assertEqual(dbstats['untranslatedsourcewords'], filestats['untranslatedsourcewords'])
        self.assertEqual(dbstats['fuzzy'], filestats['fuzzy'])
        self.assertEqual(dbstats['fuzzysourcewords'], filestats['fuzzysourcewords'])
        self.assertEqual(dbstats['translated'], filestats['translated'])
        self.assertEqual(dbstats['translatedsourcewords'], filestats['translatedsourcewords'])
        self.assertEqual(dbstats['translatedtargetwords'], filestats['translatedtargetwords'])


class XHRTestCase(PootleTestCase):
    """
    Base class for testing the XHR views.
    """
    def setUp(self):
        # FIXME: We should test on a bigger dataset (with a fixture maybe)
        super(XHRTestCase, self).setUp()
        self.store = Store.objects.get(pootle_path="/af/tutorial/pootle.po")
        self.unit = self.store.units[0]
        self.uid = self.unit.id
        self.bad_uid = 69696969
        self.path = self.store.pootle_path
        self.bad_path = "/foo/bar/baz.po"
        self.post_data = {'id': self.uid,
                          'index': 1,
                          'path': self.path,
                          'pootle_path': self.path,
                          'store': self.path,
                          'source_f_0': 'fish',
                          'target_f_0': 'arraina'}

    #
    # Tests for the get_tp_metadata() view.
    #
    def test_get_tp_metadata_bad_request(self):
        """Not an AJAX request, should return HTTP 400."""
        r = self.client.get("%(pootle_path)s/meta/%(uid)s" %\
                            {'pootle_path': self.path,
                             'uid': self.uid})
        self.assertEqual(r.status_code, 400)

    def test_get_tp_metadata_response_ok(self):
        """AJAX request, should return HTTP 200."""
        r = self.client.get("%(pootle_path)s/meta/%(uid)s" %\
                            {'pootle_path': self.path,
                             'uid': self.uid},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)

    def test_get_tp_metadata_bad_store(self):
        """Checks for store correctness when passing an invalid path."""
        r = self.client.get("%(pootle_path)s/meta/%(uid)s" %\
                            {'pootle_path': self.bad_path,
                             'uid': self.uid},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)
        j = simplejson.loads(r.content)
        self.assertFalse(j['success'])

    def test_get_tp_metadata_bad_unit(self):
        """Checks for store correctness when passing an invalid path."""
        r = self.client.get("%(pootle_path)s/meta/%(uid)s" %\
                            {'pootle_path': self.path,
                             'uid': self.bad_uid},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)
        j = simplejson.loads(r.content)
        self.assertFalse(j['success'])

    def test_get_tp_metadata_bad_store_unit(self):
        """Checks for store/unit correctness when passing an invalid path/uid."""
        r = self.client.get("%(pootle_path)s/meta/%(uid)s" %\
                            {'pootle_path': self.bad_path,
                             'uid': self.bad_uid},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)
        j = simplejson.loads(r.content)
        self.assertFalse(j['success'])

    def test_get_tp_metadata_good_response(self):
        """Checks for returned data correctness."""
        r = self.client.get("%(pootle_path)s/meta/%(uid)s" %\
                            {'pootle_path': self.path,
                             'uid': self.uid},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)
        j = simplejson.loads(r.content)
        self.assertTrue(j['success'])
        self.assertTrue(len(j['meta']) == 4)
        self.assertTrue(len(j['pager']) == 10)

    #
    # Tests for the get_view_units() view.
    #
    def test_get_view_units_bad_request(self):
        """Not an AJAX request, should return HTTP 400."""
        r = self.client.get("%(pootle_path)s/view" %\
                            {'pootle_path': self.path})
        self.assertEqual(r.status_code, 400)

    def test_get_view_units_response_ok(self):
        """AJAX request, should return HTTP 200."""
        r = self.client.get("%(pootle_path)s/view" %\
                            {'pootle_path': self.path},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)

    def test_get_view_units_bad_store(self):
        """Checks for store correctness when passing an invalid path."""
        r = self.client.get("%(pootle_path)s/view" %\
                            {'pootle_path': self.bad_path},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)
        j = simplejson.loads(r.content)
        self.assertFalse(j['success'])

    def test_get_view_units_good_response(self):
        """Checks for unit and returned data correctness."""
        r = self.client.get("%(pootle_path)s/view" %\
                            {'pootle_path': self.path},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)
        j = simplejson.loads(r.content)
        self.assertTrue(j['success'])
        unit_rows = self.profile.get_unit_rows()
        self.assertTrue(len(j['units']) <= unit_rows)

    #
    # Tests for the get_edit_unit() view.
    #
    def test_get_edit_unit_bad_request(self):
        """Not an AJAX request, should return HTTP 400."""
        r = self.client.get("%(pootle_path)s/edit/%(uid)s" %\
                            {'pootle_path': self.path,
                             'uid': self.uid})
        self.assertEqual(r.status_code, 400)

    def test_get_edit_unit_response_ok(self):
        """AJAX request, should return HTTP 200."""
        r = self.client.get("%(pootle_path)s/edit/%(uid)s" %\
                            {'pootle_path': self.path,
                             'uid': self.uid},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)

    def test_get_edit_unit_bad_store(self):
        """Checks for store correctness when passing an invalid path."""
        r = self.client.get("%(pootle_path)s/edit/%(uid)s" %\
                            {'pootle_path': self.bad_path,
                             'uid': self.uid},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 404)

    def test_get_edit_unit_bad_unit(self):
        """Checks for unit correctness when passing an invalid uid."""
        r = self.client.get("%(pootle_path)s/edit/%(uid)s" %\
                            {'pootle_path': self.path,
                             'uid': self.bad_uid},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 404)

    def test_get_edit_unit_bad_store_unit(self):
        """Checks for store/unit correctness when passing an invalid path/uid."""
        r = self.client.get("%(pootle_path)s/edit/%(uid)s" %\
                            {'pootle_path': self.bad_path,
                             'uid': self.bad_uid},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 404)

    def test_get_edit_unit_good_response(self):
        """Checks for returned data correctness."""
        r = self.client.get("%(pootle_path)s/edit/%(uid)s" %\
                            {'pootle_path': self.path,
                             'uid': self.uid},
                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'unit/edit.html')

    #
    # Tests for the process_submit() view.
    #
    def test_process_submit_bad_request(self):
        """Not an AJAX request, should return HTTP 400."""
        for m in ("submission", "suggestion"):
            r = self.client.get("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.path,
                                 'uid': self.uid,
                                 'method': m})
            self.assertEqual(r.status_code, 400)

    def test_process_submit_response_ok(self):
        """AJAX request, should return HTTP 200."""
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.path,
                                 'uid': self.uid,
                                 'method': m},
                                self.post_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)

    def test_process_submit_bad_store(self):
        """Checks for store correctness when passing an invalid path."""
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.bad_path,
                                 'uid': self.uid,
                                 'method': m},
                                self.post_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)
            j = simplejson.loads(r.content)
            self.assertFalse(j['success'])

    def test_process_submit_bad_unit(self):
        """Checks for unit correctness when passing an invalid uid."""
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.path,
                                 'uid': self.bad_uid,
                                 'method': m},
                                self.post_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)
            j = simplejson.loads(r.content)
            self.assertFalse(j['success'])

    def test_process_submit_bad_store_unit(self):
        """Checks for store/unit correctness when passing an invalid path/uid."""
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.bad_path,
                                 'uid': self.bad_uid,
                                 'method': m},
                                self.post_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)
            j = simplejson.loads(r.content)
            self.assertFalse(j['success'])

    def test_process_submit_bad_form(self):
        """Checks for form correctness when bad POST data is passed."""
        form_data = self.post_data
        del(form_data['index'])
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.path,
                                 'uid': self.uid,
                                 'method': m},
                                form_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)
            j = simplejson.loads(r.content)
            self.assertFalse(j['success'])

    def test_process_submit_good_response(self):
        """Checks for returned data correctness."""
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.path,
                                 'uid': self.uid,
                                 'method': m},
                                self.post_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)
            j = simplejson.loads(r.content)
            self.assertTrue(j['success'])
            self.assertTrue(type(j['new_uid']) == types.IntType)


class XHRTestAnonymous(XHRTestCase):
    """
    Tests the XHR views as an anonymous user.
    """
    def setUp(self):
        super(XHRTestAnonymous, self).setUp()
        self.user = User.objects.get(username='nobody')
        self.profile = get_profile(self.user)

    #
    # Overriden tests for process_submit()
    # As we are anonymous users, we will always get a captcha
    #
    def test_process_submit_bad_store(self):
        """Checks for store correctness when passing an invalid path."""
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.bad_path,
                                 'uid': self.uid,
                                 'method': m},
                                self.post_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)
            j = simplejson.loads(r.content)
            self.assertTrue('captcha' in j.keys())

    def test_process_submit_bad_unit(self):
        """Checks for unit correctness when passing an invalid uid."""
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.path,
                                 'uid': self.bad_uid,
                                 'method': m},
                                self.post_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)
            j = simplejson.loads(r.content)
            self.assertTrue('captcha' in j.keys())

    def test_process_submit_bad_store_unit(self):
        """Checks for store/unit correctness when passing an invalid path/uid."""
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.bad_path,
                                 'uid': self.bad_uid,
                                 'method': m},
                                self.post_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)
            j = simplejson.loads(r.content)
            self.assertTrue('captcha' in j.keys())

    def test_process_submit_bad_form(self):
        """Checks for form correctness when bad POST data is passed."""
        form_data = self.post_data
        del(form_data['index'])
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.path,
                                 'uid': self.uid,
                                 'method': m},
                                form_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)
            j = simplejson.loads(r.content)
            self.assertTrue('captcha' in j.keys())

    def test_process_submit_good_response(self):
        """Checks for returned data correctness."""
        for m in ("submission", "suggestion"):
            r = self.client.post("%(pootle_path)s/process/%(uid)s/%(method)s" %\
                                {'pootle_path': self.path,
                                 'uid': self.uid,
                                 'method': m},
                                self.post_data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r.status_code, 200)
            j = simplejson.loads(r.content)
            self.assertTrue('captcha' in j.keys())


class XHRTestNobody(XHRTestCase):
    """
    Tests the XHR views as a non-privileged user.
    """
    def setUp(self):
        super(XHRTestNobody, self).setUp()
        self.user = User.objects.get(username='nonpriv')
        self.profile = get_profile(self.user)
        self.client.login(username='nonpriv', password='nonpriv')


class XHRTestAdmin(XHRTestCase):
    """
    Tests the XHR views as admin user.
    """
    def setUp(self):
        super(XHRTestAdmin, self).setUp()
        self.user = User.objects.get(username='admin')
        self.profile = get_profile(self.user)
        self.client.login(username='admin', password='admin')
