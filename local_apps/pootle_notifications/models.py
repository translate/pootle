
import datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class LanguageNoticeManager(models.Manager):
    def get_notices(self, object_id, content_id):
        notices = self.extra(where=['object_id = %s AND content_type_id = %s'], params=[object_id, content_id])
        return notices


class LanguageNotice(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    message = models.TextField(_('message'))
    added = models.DateTimeField(_('added'), default=datetime.datetime.now)
    
    objects = LanguageNoticeManager()

    def __unicode__(self):
        return self.message

    class Meta:
        ordering = ["-added"]
        verbose_name = _("language notice")
        verbose_name_plural = _("language notices")


