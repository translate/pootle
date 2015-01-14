# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import connection, models
from django.contrib.contenttypes.models import ContentType


class Migration(SchemaMigration):
    depends_on = (
        ("accounts", "0004_drop_pootle_app_pootleprofile_ctype"),
    )

    def forwards(self, orm):
        ContentType.objects.filter(app_label='taggit', model='tag').delete()
        ContentType.objects.filter(app_label='taggit', model='taggeditem').delete()

        if u'taggit_taggeditem' in connection.introspection.table_names():
            # Deleting model 'TaggedItem'
            db.delete_table(u'taggit_taggeditem')

        if u'taggit_tag' in connection.introspection.table_names():
            ## Deleting model 'Tag'
            db.delete_table(u'taggit_tag')


    def backwards(self, orm):
        pass


    models = {

    }

    complete_apps = ['pootle_tagging']
