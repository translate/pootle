# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'TranslationProject.fuzzy_wordcount'
        db.delete_column('pootle_app_translationproject', 'fuzzy_wordcount')

        # Deleting field 'TranslationProject.suggestion_count'
        db.delete_column('pootle_app_translationproject', 'suggestion_count')

        # Deleting field 'TranslationProject.last_submission'
        db.delete_column('pootle_app_translationproject', 'last_submission_id')

        # Deleting field 'TranslationProject.translated_wordcount'
        db.delete_column('pootle_app_translationproject', 'translated_wordcount')

        # Deleting field 'TranslationProject.total_wordcount'
        db.delete_column('pootle_app_translationproject', 'total_wordcount')

        # Deleting field 'TranslationProject.last_unit'
        db.delete_column('pootle_app_translationproject', 'last_unit_id')

        # Deleting field 'TranslationProject.failing_critical_count'
        db.delete_column('pootle_app_translationproject', 'failing_critical_count')


    def backwards(self, orm):
        # Adding field 'TranslationProject.fuzzy_wordcount'
        db.add_column('pootle_app_translationproject', 'fuzzy_wordcount',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True),
                      keep_default=False)

        # Adding field 'TranslationProject.suggestion_count'
        db.add_column('pootle_app_translationproject', 'suggestion_count',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True),
                      keep_default=False)

        # Adding field 'TranslationProject.last_submission'
        db.add_column('pootle_app_translationproject', 'last_submission',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pootle_statistics.Submission'], unique=True, null=True),
                      keep_default=False)

        # Adding field 'TranslationProject.translated_wordcount'
        db.add_column('pootle_app_translationproject', 'translated_wordcount',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True),
                      keep_default=False)

        # Adding field 'TranslationProject.total_wordcount'
        db.add_column('pootle_app_translationproject', 'total_wordcount',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True),
                      keep_default=False)

        # Adding field 'TranslationProject.last_unit'
        db.add_column('pootle_app_translationproject', 'last_unit',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pootle_store.Unit'], unique=True, null=True),
                      keep_default=False)

        # Adding field 'TranslationProject.failing_critical_count'
        db.add_column('pootle_app_translationproject', 'failing_critical_count',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True),
                      keep_default=False)


    models = {
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
        u'pootle_translationproject.translationproject': {
            'Meta': {'unique_together': "(('language', 'project'),)", 'object_name': 'TranslationProject', 'db_table': "'pootle_app_translationproject'"},
            'description': ('pootle.core.markup.fields.MarkupField', [], {'blank': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_language.Language']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_project.Project']"}),
            'real_path': ('django.db.models.fields.FilePathField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['pootle_translationproject']