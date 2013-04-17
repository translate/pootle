# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'LegalPage.slug'
        db.delete_column('staticpages_legalpage', 'slug')


        # Changing field 'LegalPage.virtual_path'
        db.alter_column('staticpages_legalpage', 'virtual_path', self.gf('django.db.models.fields.CharField')(max_length=100))

    def backwards(self, orm):
        # Adding field 'LegalPage.slug'
        db.add_column('staticpages_legalpage', 'slug',
                      self.gf('django.db.models.fields.SlugField')(default='', max_length=50),
                      keep_default=False)


        # Changing field 'LegalPage.virtual_path'
        db.alter_column('staticpages_legalpage', 'virtual_path', self.gf('django.db.models.fields.CharField')(max_length=100, null=True))

    models = {
        'staticpages.legalpage': {
            'Meta': {'object_name': 'LegalPage'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'body': ('pootle.core.markup.fields.MarkupField', [], {'blank': 'True'}),
            'display_on_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'virtual_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'})
        }
    }

    complete_apps = ['staticpages']