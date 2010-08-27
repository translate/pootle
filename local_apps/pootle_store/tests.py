import time

from translate.storage import factory
from translate.storage import statsdb

from pootle.tests import PootleTestCase
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
