# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import connection, models
from django.contrib.contenttypes.models import ContentType


class Migration(SchemaMigration):
    depends_on = (
        ("pootle_app", "0014_drop_duplicate_directory_pootle_paths"),
    )

    def forwards(self, orm):
        if u'pootle_notifications_notice' in connection.introspection.table_names():
            # Deleting model 'Notice'
            ContentType.objects.filter(app_label='pootle_notifications', model='notice').delete()
            db.delete_table(u'pootle_notifications_notice')


    def backwards(self, orm):
        pass


    models = {}

    complete_apps = ['pootle_notifications']
