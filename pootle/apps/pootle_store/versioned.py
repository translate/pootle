
from pootle.core.proxy import BaseProxy
from pootle_statistics.models import Submission, SubmissionFields


class StoreVersion(BaseProxy):
    pass


class VersionedStore(object):
    version_class = StoreVersion

    def __init__(self, store):
        self.store = store

    @property
    def current_store(self):
        return StoreVersion(
            self.store.deserialize(
                self.store.serialize(
                    include_obsolete=True,
                    raw=True)))

    def _revert_state(self, unit, sub):
        if sub.old_value == "50":
            unit.markfuzzy()
        if sub.old_value == "-100":
            unit.makeobsolete()
        if sub.old_value in ["0", "200"]:
            if sub.new_value == "50":
                unit.markfuzzy(False)
            if sub.new_value == "-100":
                unit.resurrect()

    def at_revision(self, revision):
        store = self.current_store
        subs = Submission.objects.filter(
            unit__store=self.store).filter(
                revision__gt=revision).order_by(
                    "revision", "creation_time")
        checking = dict(target=[], state=[])
        unit_creation = self.store.unit_set.filter(
            unit_source__creation_revision__gt=revision).values_list(
                "unitid", flat=True)
        for unit in unit_creation:
            del store.units[store.units.index(store.findid(unit))]
            del store.id_index[unit]

        for sub in subs.iterator():
            unit = store.findid(sub.unit.getid())
            if not unit:
                continue
            if sub.field == SubmissionFields.TARGET:
                if sub.unit.pk in checking["target"]:
                    continue
                checking["target"].append(sub.unit.pk)
                unit.target = sub.old_value
            if sub.field == SubmissionFields.STATE:
                if sub.unit.pk in checking["state"]:
                    continue
                checking["state"].append(sub.unit.pk)
                self._revert_state(unit, sub)
        return store
