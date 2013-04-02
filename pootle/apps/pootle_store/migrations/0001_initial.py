# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'QualityCheck'
        db.create_table('pootle_store_qualitycheck', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pootle_store.Unit'])),
            ('category', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('false_positive', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal('pootle_store', ['QualityCheck'])

        # Adding model 'Suggestion'
        db.create_table('pootle_store_suggestion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('target_f', self.gf('pootle_store.fields.MultiStringField')()),
            ('target_hash', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pootle_store.Unit'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pootle_profile.PootleProfile'], null=True)),
            ('translator_comment_f', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('pootle_store', ['Suggestion'])

        # Adding unique constraint on 'Suggestion', fields ['unit', 'target_hash']
        db.create_unique('pootle_store_suggestion', ['unit_id', 'target_hash'])

        # Adding model 'Unit'
        db.create_table('pootle_store_unit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('store', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pootle_store.Store'])),
            ('index', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('unitid', self.gf('django.db.models.fields.TextField')()),
            ('unitid_hash', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('source_f', self.gf('pootle_store.fields.MultiStringField')(null=True)),
            ('source_hash', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('source_wordcount', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('source_length', self.gf('django.db.models.fields.SmallIntegerField')(default=0, db_index=True)),
            ('target_f', self.gf('pootle_store.fields.MultiStringField')(null=True, blank=True)),
            ('target_wordcount', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('target_length', self.gf('django.db.models.fields.SmallIntegerField')(default=0, db_index=True)),
            ('developer_comment', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('translator_comment', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('locations', self.gf('django.db.models.fields.TextField')(null=True)),
            ('context', self.gf('django.db.models.fields.TextField')(null=True)),
            ('state', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('mtime', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, db_index=True, blank=True)),
            ('submitted_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submitted', null=True, to=orm['pootle_profile.PootleProfile'])),
            ('submitted_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, db_index=True, blank=True)),
            ('commented_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='commented', null=True, to=orm['pootle_profile.PootleProfile'])),
            ('commented_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('pootle_store', ['Unit'])

        # Adding unique constraint on 'Unit', fields ['store', 'unitid_hash']
        db.create_unique('pootle_store_unit', ['store_id', 'unitid_hash'])

        # Adding model 'Store'
        db.create_table('pootle_store_store', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('pootle_store.fields.TranslationStoreField')(max_length=255, db_index=True)),
            ('pending', self.gf('pootle_store.fields.TranslationStoreField')(ignore='.pending', max_length=255)),
            ('tm', self.gf('pootle_store.fields.TranslationStoreField')(ignore='.tm', max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='child_stores', to=orm['pootle_app.Directory'])),
            ('translation_project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='stores', to=orm['pootle_translationproject.TranslationProject'])),
            ('pootle_path', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('sync_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1, 1, 1, 0, 0))),
            ('state', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
        ))
        db.send_create_signal('pootle_store', ['Store'])

        # Adding unique constraint on 'Store', fields ['parent', 'name']
        db.create_unique('pootle_store_store', ['parent_id', 'name'])


    def backwards(self, orm):
        # Removing unique constraint on 'Store', fields ['parent', 'name']
        db.delete_unique('pootle_store_store', ['parent_id', 'name'])

        # Removing unique constraint on 'Unit', fields ['store', 'unitid_hash']
        db.delete_unique('pootle_store_unit', ['store_id', 'unitid_hash'])

        # Removing unique constraint on 'Suggestion', fields ['unit', 'target_hash']
        db.delete_unique('pootle_store_suggestion', ['unit_id', 'target_hash'])

        # Deleting model 'QualityCheck'
        db.delete_table('pootle_store_qualitycheck')

        # Deleting model 'Suggestion'
        db.delete_table('pootle_store_suggestion')

        # Deleting model 'Unit'
        db.delete_table('pootle_store_unit')

        # Deleting model 'Store'
        db.delete_table('pootle_store_store')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'pootle_app.directory': {
            'Meta': {'ordering': "['name']", 'object_name': 'Directory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_dirs'", 'null': 'True', 'to': "orm['pootle_app.Directory']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'pootle_language.language': {
            'Meta': {'ordering': "['code']", 'object_name': 'Language', 'db_table': "'pootle_app_language'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nplurals': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'pluralequation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'specialchars': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'pootle_profile.pootleprofile': {
            'Meta': {'object_name': 'PootleProfile', 'db_table': "'pootle_app_pootleprofile'"},
            'alt_src_langs': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_alt_src_langs'", 'blank': 'True', 'db_index': 'True', 'to': "orm['pootle_language.Language']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_height': ('django.db.models.fields.SmallIntegerField', [], {'default': '5'}),
            'languages': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_languages'", 'blank': 'True', 'db_index': 'True', 'to': "orm['pootle_language.Language']"}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'to': "orm['pootle_project.Project']", 'symmetrical': 'False', 'blank': 'True'}),
            'ui_lang': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'unit_rows': ('django.db.models.fields.SmallIntegerField', [], {'default': '9'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'pootle_project.project': {
            'Meta': {'ordering': "['code']", 'object_name': 'Project', 'db_table': "'pootle_app_project'"},
            'checkstyle': ('django.db.models.fields.CharField', [], {'default': "'standard'", 'max_length': '50'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignoredfiles': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'localfiletype': ('django.db.models.fields.CharField', [], {'default': "'po'", 'max_length': '50'}),
            'report_target': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'source_language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_language.Language']"}),
            'treestyle': ('django.db.models.fields.CharField', [], {'default': "'auto'", 'max_length': '20'})
        },
        'pootle_store.qualitycheck': {
            'Meta': {'object_name': 'QualityCheck'},
            'category': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'false_positive': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_store.Unit']"})
        },
        'pootle_store.store': {
            'Meta': {'ordering': "['pootle_path']", 'unique_together': "(('parent', 'name'),)", 'object_name': 'Store'},
            'file': ('pootle_store.fields.TranslationStoreField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_stores'", 'to': "orm['pootle_app.Directory']"}),
            'pending': ('pootle_store.fields.TranslationStoreField', [], {'ignore': "'.pending'", 'max_length': '255'}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'sync_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1, 1, 1, 0, 0)'}),
            'tm': ('pootle_store.fields.TranslationStoreField', [], {'ignore': "'.tm'", 'max_length': '255'}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stores'", 'to': "orm['pootle_translationproject.TranslationProject']"})
        },
        'pootle_store.suggestion': {
            'Meta': {'unique_together': "(('unit', 'target_hash'),)", 'object_name': 'Suggestion'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'target_f': ('pootle_store.fields.MultiStringField', [], {}),
            'target_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'translator_comment_f': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_store.Unit']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_profile.PootleProfile']", 'null': 'True'})
        },
        'pootle_store.unit': {
            'Meta': {'ordering': "['store', 'index']", 'unique_together': "(('store', 'unitid_hash'),)", 'object_name': 'Unit'},
            'commented_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'commented'", 'null': 'True', 'to': "orm['pootle_profile.PootleProfile']"}),
            'commented_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'context': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'developer_comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'locations': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source_f': ('pootle_store.fields.MultiStringField', [], {'null': 'True'}),
            'source_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'source_length': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'source_wordcount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_store.Store']"}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted'", 'null': 'True', 'to': "orm['pootle_profile.PootleProfile']"}),
            'submitted_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'target_f': ('pootle_store.fields.MultiStringField', [], {'null': 'True', 'blank': 'True'}),
            'target_length': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'target_wordcount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'translator_comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'unitid': ('django.db.models.fields.TextField', [], {}),
            'unitid_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'})
        },
        'pootle_translationproject.translationproject': {
            'Meta': {'unique_together': "(('language', 'project'),)", 'object_name': 'TranslationProject', 'db_table': "'pootle_app_translationproject'"},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'description_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_language.Language']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_project.Project']"}),
            'real_path': ('django.db.models.fields.FilePathField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['pootle_store']