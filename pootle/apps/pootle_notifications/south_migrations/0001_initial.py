# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Notice'
        db.create_table(u'pootle_notifications_notice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('directory', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pootle_app.Directory'])),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, db_index=True, blank=True)),
        ))
        db.send_create_signal(u'pootle_notifications', ['Notice'])


    def backwards(self, orm):
        # Deleting model 'Notice'
        db.delete_table(u'pootle_notifications_notice')


    models = {
        'pootle_app.directory': {
            'Meta': {'ordering': "['name']", 'object_name': 'Directory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obsolete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_dirs'", 'null': 'True', 'to': "orm['pootle_app.Directory']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'pootle_notifications.notice': {
            'Meta': {'ordering': "['-added']", 'object_name': 'Notice'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'directory': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_app.Directory']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['pootle_notifications']