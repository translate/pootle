# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import connection, models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'LegalPage'
        if 'staticpages_legalpage' not in connection.introspection.table_names():
            if 'legalpages_legalpage' in connection.introspection.table_names():
                # Migrate to the new app name, including content types
                db.rename_table('legalpages_legalpage', 'staticpages_legalpage')

                if not db.dry_run:
                    content_types = orm['contenttypes.ContentType'].objects \
                    .filter(app_label='legalpages')
                    content_types.update(app_label='staticpages')
            else:
                # Tables are not there, let's create them for the first time
                db.create_table('staticpages_legalpage', (
                    ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                    ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
                    ('display_on_register', self.gf('django.db.models.fields.BooleanField')(default=False)),
                    ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
                    ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
                    ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
                    ('body', self.gf('django.db.models.fields.TextField')(blank=True)),
                    ('body_html', self.gf('django.db.models.fields.TextField')(blank=True)),
                ))

                db.send_create_signal('staticpages', ['LegalPage'])


    def backwards(self, orm):
        # Deleting model 'LegalPage'
        db.delete_table('staticpages_legalpage')


    models = {
        'staticpages.legalpage': {
            'Meta': {'object_name': 'LegalPage'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'body_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'display_on_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['staticpages']
