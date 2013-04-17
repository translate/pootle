# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'LegalPage.body_html'
        db.delete_column('staticpages_legalpage', 'body_html')


        # Changing field 'LegalPage.body'
        db.alter_column('staticpages_legalpage', 'body', self.gf('pootle.core.markup.fields.MarkupField')())

    def backwards(self, orm):
        # Adding field 'LegalPage.body_html'
        db.add_column('staticpages_legalpage', 'body_html',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)


        # Changing field 'LegalPage.body'
        db.alter_column('staticpages_legalpage', 'body', self.gf('django.db.models.fields.TextField')())

    models = {
        'staticpages.legalpage': {
            'Meta': {'object_name': 'LegalPage'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'body': ('pootle.core.markup.fields.MarkupField', [], {'blank': 'True'}),
            'display_on_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': "''", 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['staticpages']