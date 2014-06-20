# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.conf import settings
from django.db import models

AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "auth.User")


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Suggestion'
        db.create_table('pootle_app_suggestion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('unit', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='pending', max_length=16, db_index=True)),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('review_time', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
        ))
        db.send_create_signal('pootle_app', ['Suggestion'])

        # Adding model 'Directory'
        db.create_table('pootle_app_directory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='child_dirs', null=True, to=orm['pootle_app.Directory'])),
            ('pootle_path', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('pootle_app', ['Directory'])

        # Adding model 'PermissionSet'
        db.create_table('pootle_app_permissionset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('directory', self.gf('django.db.models.fields.related.ForeignKey')(related_name='permission_sets', to=orm['pootle_app.Directory'])),
        ))
        db.send_create_signal('pootle_app', ['PermissionSet'])

        # Adding M2M table for field positive_permissions on 'PermissionSet'
        db.create_table('pootle_app_permissionset_positive_permissions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permissionset', models.ForeignKey(orm['pootle_app.permissionset'], null=False)),
            ('permission', models.ForeignKey(orm['auth.permission'], null=False))
        ))
        db.create_unique('pootle_app_permissionset_positive_permissions', ['permissionset_id', 'permission_id'])

        # Adding M2M table for field negative_permissions on 'PermissionSet'
        db.create_table('pootle_app_permissionset_negative_permissions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('permissionset', models.ForeignKey(orm['pootle_app.permissionset'], null=False)),
            ('permission', models.ForeignKey(orm['auth.permission'], null=False))
        ))
        db.create_unique('pootle_app_permissionset_negative_permissions', ['permissionset_id', 'permission_id'])


    def backwards(self, orm):
        # Deleting model 'Suggestion'
        db.delete_table('pootle_app_suggestion')

        # Deleting model 'Directory'
        db.delete_table('pootle_app_directory')

        # Deleting model 'PermissionSet'
        db.delete_table('pootle_app_permissionset')

        # Removing M2M table for field positive_permissions on 'PermissionSet'
        db.delete_table('pootle_app_permissionset_positive_permissions')

        # Removing M2M table for field negative_permissions on 'PermissionSet'
        db.delete_table('pootle_app_permissionset_negative_permissions')


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
        'accounts.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
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
        'pootle_app.permissionset': {
            'Meta': {'unique_together': "(('profile', 'directory'),)", 'object_name': 'PermissionSet'},
            'directory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permission_sets'", 'to': "orm['pootle_app.Directory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'negative_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'permission_sets_negative'", 'symmetrical': 'False', 'to': "orm['auth.Permission']"}),
            'positive_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'related_name': "'permission_sets_positive'", 'symmetrical': 'False', 'to': "orm['auth.Permission']"}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.User']"})
        },
        'pootle_app.suggestion': {
            'Meta': {'object_name': 'Suggestion'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'review_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '16', 'db_index': 'True'}),
            'unit': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
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

    complete_apps = ['pootle_app']
