# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import connection, models
from django.contrib.contenttypes.models import ContentType


class Migration(SchemaMigration):
    depends_on = (
        ("accounts", "0003_auto__inherit_from_permissionsmixin"),
    )

    def forwards(self, orm):
        if u'pootle_tagging_itemwithgoal' in connection.introspection.table_names():
            # Deleting model 'ItemWithGoal'
            ContentType.objects.filter(app_label='pootle_tagging', model='itemwithgoal').delete()
            db.delete_table(u'pootle_tagging_itemwithgoal')

        if u'pootle_tagging_goal' in connection.introspection.table_names():
            # Deleting model 'Goal'
            ContentType.objects.filter(app_label='pootle_tagging', model='goal').delete()
            db.delete_table(u'pootle_tagging_goal')


    def backwards(self, orm):
        # Adding model 'Goal'
        db.create_table(u'pootle_tagging_goal', (
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=100, unique=True)),
            ('description', self.gf('pootle.core.markup.fields.MarkupField')(blank=True)),
            ('project_goal', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('directory', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pootle_app.Directory'], unique=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, unique=True)),
        ))
        db.send_create_signal('pootle_tagging', ['Goal'])

        # Adding model 'ItemWithGoal'
        db.create_table(u'pootle_tagging_itemwithgoal', (
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items_with_goal', to=orm['pootle_tagging.Goal'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'pootle_tagging_itemwithgoal_tagged_items', to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
        ))
        db.send_create_signal('pootle_tagging', ['ItemWithGoal'])


    models = {
        
    }

    complete_apps = ['pootle_tagging']
