
from django.db import models

from pootle_language.models import Language


class AbstractRemoteSite(models.Model):
    url = models.URLField()
    type = models.CharField(max_length=32)
    sync_frequency = models.IntegerField()
    last_sync = models.DateTimeField()
    update_frequency = models.IntegerField()

    class Meta(object):
        abstract = True


class AbstractRemoteProject(models.Model):
    code = models.CharField(
        db_index=True,
        max_length=255,
        null=False,
        blank=False)
    fullname = models.CharField(
        db_index=True,
        max_length=255,
        null=False,
        blank=False)
    languages = models.ManyToManyField(Language)

    class Meta(object):
        abstract = True
