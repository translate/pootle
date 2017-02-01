
from django.db.models.signals import post_save
from django.dispatch import receiver

from pootle.core.signals import changed

from .models import Store, Unit
from .utils import UnitEvent


@receiver(post_save, sender=Unit)
def unit_save_handler(**kwargs):
    unit = kwargs["instance"]
    original = None
    updates = {}
    diffable = ["source", "target", "state"]
    if kwargs["created"]:
        changed.send(Unit, instance=unit, updates=dict(created=True))
        return
    original = unit._at_last_save
    if original:
        for change in diffable:
            ov = getattr(original, change)
            nv = getattr(unit, change)
            if ov != nv:
                updates[change] = ov
    if updates:
        changed.send(Unit, instance=unit, updates=updates)


@receiver(changed, sender=Unit)
def unit_changed_handler(**kwargs):
    unit = kwargs["instance"]
    UnitEvent(unit).update(**kwargs["updates"])


@receiver(changed, sender=Store)
def store_changed_handler(**kwargs):
    # unit = kwargs["instance"]
    # updates = kwargs["updates"]
    pass
