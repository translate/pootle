# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import connection, models
from django.contrib.contenttypes.models import ContentType


class Migration(SchemaMigration):

    def forwards(self, orm):
        if u'pootle_app_pootlesite' in connection.introspection.table_names():
            # Deleting model 'PootleSite'
            ContentType.objects.filter(app_label='pootle_app', model='pootlesite').delete()
            db.delete_table(u'pootle_app_pootlesite')


    def backwards(self, orm):
        pass


    models = {
        u'accounts.user': {
            'Meta': {'object_name': 'User'},
            '_unit_rows': ('django.db.models.fields.SmallIntegerField', [], {'default': '9', 'db_column': "'unit_rows'"}),
            'alt_src_langs': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_alt_src_langs'", 'blank': 'True', 'db_index': 'True', 'to': u"orm['pootle_language.Language']"}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'pootle_app.directory': {
            'Meta': {'ordering': "['name']", 'object_name': 'Directory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obsolete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_dirs'", 'null': 'True', 'to': "orm['pootle_app.Directory']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'pootle_app.permissionset': {
            'Meta': {'unique_together': "(('user', 'directory'),)", 'object_name': 'PermissionSet'},
            'directory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permission_sets'", 'to': "orm['pootle_app.Directory']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'negative_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'permission_sets_negative'", 'symmetrical': 'False', 'to': u"orm['auth.Permission']"}),
            'positive_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'related_name': "'permission_sets_positive'", 'symmetrical': 'False', 'to': u"orm['auth.Permission']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.User']"})
        },
        'pootle_app.pootleconfig': {
            'Meta': {'object_name': 'PootleConfig'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ptl_build': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ttk_build': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'pootle_language.language': {
            'Meta': {'ordering': "['code']", 'object_name': 'Language', 'db_table': "'pootle_app_language'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'description': ('pootle.core.markup.fields.MarkupField', [], {'blank': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nplurals': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'pluralequation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'specialchars': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['pootle_app']
