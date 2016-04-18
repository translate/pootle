
from pootle.core.delegate import extracted_path, unit_priority
from pootle.core.plugin import getter
from pootle_translationproject.views import TPTranslateView

from .helpers import extract_vfolder_from_path
from .models import VirtualFolderTreeItem


def _extract_path(path):
    vfolder, new_path = extract_vfolder_from_path(
        path,
        vfti=VirtualFolderTreeItem.objects.select_related(
            "directory", "vfolder"))
    if vfolder:
        return new_path, ("%s/" % vfolder.name), dict(vfolder=vfolder)


@getter(extracted_path, sender=str)
def extract_string_path(sender, **kwargs):
    return _extract_path(kwargs["instance"])


@getter(extracted_path, sender=TPTranslateView)
def extract_tp_translate_path(sender, **kwargs):
    return _extract_path(kwargs["view"].request_path)


@getter(unit_priority)
def calculate_vfolder_priority(sender, **kwargs):
    priority = (
        kwargs["instance"].vfolders.order_by("-priority")
                          .values_list("priority", flat=True)
                          .first())
    if priority is None:
        return 1.0
    return priority
