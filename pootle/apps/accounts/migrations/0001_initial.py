# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import connection, models


class Migration(SchemaMigration):

    def forwards(self, orm):
        if "auth_user" not in connection.introspection.table_names():
            # Fresh installations of Pootle will not have an auth_user table.
            db.create_table("accounts_user", (
                (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
                ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
                ('email', self.gf('django.db.models.fields.EmailField')(max_length=255)),
                ('full_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
                ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
                ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
                ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ))
            db.send_create_signal("accounts", ["User"])
            # We're done here
            return

        # We now have a full_name column instead of first_name and last_name
        db.add_column("auth_user", "full_name",
                      self.gf("django.db.models.fields.CharField")(default='', max_length=255),
                      keep_default=False)
        if db.backend_name == "mysql":
            db.execute("UPDATE auth_user SET full_name = CONCAT(`first_name`, ' ', `last_name`)")
        else:
            # Works in postgres and sqlite
            db.execute("UPDATE auth_user SET full_name = first_name || ' ' || last_name")

        # Delete the first_name and last_name columns now
        db.delete_column("auth_user", "first_name")
        db.delete_column("auth_user", "last_name")
        # We don't use the is_staff column either
        db.delete_column("auth_user", "is_staff")

        # Finally, rename the table to accounts_user
        db.rename_table("auth_user", "accounts_user")

    def backwards(self, orm):
        db.rename_table("accounts_user", "auth_user")

        # WARNING: full_name -> first_name + last_name is lossy!
        db.add_column("auth_user", "first_name",
                      self.gf("django.db.models.fields.CharField")(default='', max_length=30),
                      keep_default=False)
        db.add_column("auth_user", "last_name",
                      self.gf("django.db.models.fields.CharField")(default='', max_length=30),
                      keep_default=False)
        db.add_column("auth_user", "is_staff",
                      self.gf("django.db.models.fields.BooleanField")(default=False),
                      keep_default=False)

        db.delete_column("auth_user", "full_name")

    models = {
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
        }
    }

    complete_apps = ['accounts']
