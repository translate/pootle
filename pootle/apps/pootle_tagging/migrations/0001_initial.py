# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("pootle_app", "0001_initial"),
    )

    def forwards(self, orm):
        # Adding model 'Goal'
        db.create_table('pootle_tagging_goal', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100)),
            ('description', self.gf('pootle.core.markup.fields.MarkupField')(blank=True)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('project_goal', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('directory', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pootle_app.Directory'], unique=True)),
        ))
        db.send_create_signal('pootle_tagging', ['Goal'])

        # Adding model 'ItemWithGoal'
        db.create_table('pootle_tagging_itemwithgoal', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('object_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'pootle_tagging_itemwithgoal_tagged_items', to=orm['contenttypes.ContentType'])),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items_with_goal', to=orm['pootle_tagging.Goal'])),
        ))
        db.send_create_signal('pootle_tagging', ['ItemWithGoal'])


    def backwards(self, orm):
        # Deleting model 'Goal'
        db.delete_table('pootle_tagging_goal')

        # Deleting model 'ItemWithGoal'
        db.delete_table('pootle_tagging_itemwithgoal')


    models = {
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
        'pootle_tagging.goal': {
            'Meta': {'ordering': "['priority']", 'object_name': 'Goal'},
            'description': ('pootle.core.markup.fields.MarkupField', [], {'blank': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'project_goal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        'pootle_tagging.itemwithgoal': {
            'Meta': {'object_name': 'ItemWithGoal'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'pootle_tagging_itemwithgoal_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items_with_goal'", 'to': "orm['pootle_tagging.Goal']"})
        }
    }

    complete_apps = ['pootle_tagging']
