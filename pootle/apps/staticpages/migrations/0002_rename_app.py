# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import connection, models

class Migration(SchemaMigration):

    def forwards(self, orm):
        if 'legalpages_legalpage' in connection.introspection.table_names():
            if 'staticpages_legalpage' in connection.introspection.table_names():
                # Deleting model 'LegalPage' from 'legalpages' app.
                db.delete_table('legalpages_legalpage')

                if not db.dry_run:
                    content_types = orm['contenttypes.ContentType'].objects \
                    .filter(app_label='legalpages')
                    content_types.delete()
            else:
                # Migrate to the new app name, including content types
                db.rename_table('legalpages_legalpage', 'staticpages_legalpage')

                if not db.dry_run:
                    content_types = orm['contenttypes.ContentType'].objects \
                    .filter(app_label='legalpages')
                    content_types.update(app_label='staticpages')

    def backwards(self, orm):
        pass

    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'staticpages.legalpage': {
            'Meta': {'object_name': 'LegalPage'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'body_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'display_on_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['contenttypes', 'staticpages']
    symmetrical = True
