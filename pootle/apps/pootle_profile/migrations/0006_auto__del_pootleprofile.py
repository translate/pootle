# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'PootleProfile'
        db.delete_table('pootle_app_pootleprofile')

        # Removing M2M table for field alt_src_langs on 'PootleProfile'
        db.delete_table(db.shorten_name('pootle_app_pootleprofile_alt_src_langs'))


    def backwards(self, orm):
        # Adding model 'PootleProfile'
        db.create_table('pootle_app_pootleprofile', (
            ('rate', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('ui_lang', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('score', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('unit_rows', self.gf('django.db.models.fields.SmallIntegerField')(default=9)),
            ('review_rate', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('input_height', self.gf('django.db.models.fields.SmallIntegerField')(default=5)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
        ))
        db.send_create_signal('pootle_profile', ['PootleProfile'])

        # Adding M2M table for field alt_src_langs on 'PootleProfile'
        m2m_table_name = db.shorten_name('pootle_app_pootleprofile_alt_src_langs')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pootleprofile', models.ForeignKey(orm['pootle_profile.pootleprofile'], null=False)),
            ('language', models.ForeignKey(orm['pootle_language.language'], null=False))
        ))
        db.create_unique(m2m_table_name, ['pootleprofile_id', 'language_id'])


    models = {
        
    }

    complete_apps = ['pootle_profile']