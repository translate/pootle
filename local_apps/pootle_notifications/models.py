
import datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from pootle_app.models import TranslationProject, Language

class NoticeManager(models.Manager):
    def get_notices(self, obj):
        notices = self.extra(where=['object_id = %s AND content_type_id = %s'], params=[obj.object_id, obj.content_type_id])
        return notices


class Notice(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    message = models.TextField(_('message'))
    added = models.DateTimeField(_('added'), default=datetime.datetime.now)
    
    objects = NoticeManager()

    def __unicode__(self):
        return self.message

    class Meta:
        ordering = ["-added"]
        verbose_name = _("notice")
        verbose_name_plural = _("notices")

