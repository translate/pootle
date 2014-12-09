# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Store.fuzzy_wordcount'
        db.delete_column(u'pootle_store_store', 'fuzzy_wordcount')

        # Deleting field 'Store.suggestion_count'
        db.delete_column(u'pootle_store_store', 'suggestion_count')

        # Deleting field 'Store.last_submission'
        db.delete_column(u'pootle_store_store', 'last_submission_id')

        # Deleting field 'Store.translated_wordcount'
        db.delete_column(u'pootle_store_store', 'translated_wordcount')

        # Deleting field 'Store.total_wordcount'
        db.delete_column(u'pootle_store_store', 'total_wordcount')

        # Deleting field 'Store.last_unit'
        db.delete_column(u'pootle_store_store', 'last_unit_id')

        # Deleting field 'Store.failing_critical_count'
        db.delete_column(u'pootle_store_store', 'failing_critical_count')


    def backwards(self, orm):
        # Adding field 'Store.fuzzy_wordcount'
        db.add_column(u'pootle_store_store', 'fuzzy_wordcount',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True),
                      keep_default=False)

        # Adding field 'Store.suggestion_count'
        db.add_column(u'pootle_store_store', 'suggestion_count',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True),
                      keep_default=False)

        # Adding field 'Store.last_submission'
        db.add_column(u'pootle_store_store', 'last_submission',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pootle_statistics.Submission'], unique=True, null=True),
                      keep_default=False)

        # Adding field 'Store.translated_wordcount'
        db.add_column(u'pootle_store_store', 'translated_wordcount',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True),
                      keep_default=False)

        # Adding field 'Store.total_wordcount'
        db.add_column(u'pootle_store_store', 'total_wordcount',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True),
                      keep_default=False)

        # Adding field 'Store.last_unit'
        db.add_column(u'pootle_store_store', 'last_unit',
                      self.gf('django.db.models.fields.related.OneToOneField')(related_name='last_unit', unique=True, null=True, to=orm['pootle_store.Unit']),
                      keep_default=False)

        # Adding field 'Store.failing_critical_count'
        db.add_column(u'pootle_store_store', 'failing_critical_count',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True),
                      keep_default=False)


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
        },
        u'pootle_project.project': {
            'Meta': {'ordering': "['code']", 'object_name': 'Project', 'db_table': "'pootle_app_project'"},
            'checkstyle': ('django.db.models.fields.CharField', [], {'default': "'standard'", 'max_length': '50'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'description': ('pootle.core.markup.fields.MarkupField', [], {'blank': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignoredfiles': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'localfiletype': ('django.db.models.fields.CharField', [], {'default': "'po'", 'max_length': '50'}),
            'report_email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'source_language': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_language.Language']"}),
            'treestyle': ('django.db.models.fields.CharField', [], {'default': "'auto'", 'max_length': '20'})
        },
        u'pootle_statistics.submission': {
            'Meta': {'ordering': "['creation_time']", 'object_name': 'Submission', 'db_table': "'pootle_app_submission'"},
            'check': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.QualityCheck']", 'null': 'True', 'blank': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'field': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_value': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'old_value': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.User']", 'null': 'True'}),
            'suggestion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Suggestion']", 'null': 'True', 'blank': 'True'}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_translationproject.TranslationProject']"}),
            'type': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Unit']", 'null': 'True', 'blank': 'True'})
        },
        u'pootle_store.qualitycheck': {
            'Meta': {'object_name': 'QualityCheck'},
            'category': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'false_positive': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Unit']"})
        },
        u'pootle_store.store': {
            'Meta': {'ordering': "['pootle_path']", 'unique_together': "(('parent', 'name'),)", 'object_name': 'Store'},
            'file': ('pootle_store.fields.TranslationStoreField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_stores'", 'to': "orm['pootle_app.Directory']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'sync_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1, 1, 1, 0, 0)'}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stores'", 'to': u"orm['pootle_translationproject.TranslationProject']"})
        },
        u'pootle_store.suggestion': {
            'Meta': {'object_name': 'Suggestion'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'review_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviews'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '16', 'db_index': 'True'}),
            'target_f': ('pootle_store.fields.MultiStringField', [], {}),
            'target_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'translator_comment_f': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Unit']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggestions'", 'null': 'True', 'to': u"orm['accounts.User']"})
        },
        u'pootle_store.unit': {
            'Meta': {'ordering': "['store', 'index']", 'unique_together': "(('store', 'unitid_hash'),)", 'object_name': 'Unit'},
            'commented_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'commented'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'commented_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'context': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'developer_comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'locations': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source_f': ('pootle_store.fields.MultiStringField', [], {'null': 'True'}),
            'source_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'source_length': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'source_wordcount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Store']"}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'submitted_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'target_f': ('pootle_store.fields.MultiStringField', [], {'null': 'True', 'blank': 'True'}),
            'target_length': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'target_wordcount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'translator_comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'unitid': ('django.db.models.fields.TextField', [], {}),
            'unitid_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'})
        },
        u'pootle_translationproject.translationproject': {
            'Meta': {'unique_together': "(('language', 'project'),)", 'object_name': 'TranslationProject', 'db_table': "'pootle_app_translationproject'"},
            'description': ('pootle.core.markup.fields.MarkupField', [], {'blank': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'failing_critical_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'fuzzy_wordcount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_language.Language']"}),
            'last_submission': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pootle_statistics.Submission']", 'unique': 'True', 'null': 'True'}),
            'last_unit': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['pootle_store.Unit']", 'unique': 'True', 'null': 'True'}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_project.Project']"}),
            'real_path': ('django.db.models.fields.FilePathField', [], {'max_length': '100'}),
            'suggestion_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'total_wordcount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'translated_wordcount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'})
        }
    }

    complete_apps = ['pootle_store']