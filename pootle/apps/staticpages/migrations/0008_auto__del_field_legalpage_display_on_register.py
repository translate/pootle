# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'LegalPage.display_on_register'
        db.delete_column('staticpages_legalpage', 'display_on_register')


    def backwards(self, orm):
        # Adding field 'LegalPage.display_on_register'
        db.add_column('staticpages_legalpage', 'display_on_register',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    models = {
        'staticpages.legalpage': {
            'Meta': {'object_name': 'LegalPage'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'body': ('pootle.core.markup.fields.MarkupField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'virtual_path': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['staticpages']