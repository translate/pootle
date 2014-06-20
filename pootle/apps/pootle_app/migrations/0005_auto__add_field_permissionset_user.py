# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.conf import settings
from django.db import connection, models

AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "auth.User")


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'PermissionSet.user'
        db.add_column(u'pootle_app_permissionset', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm[AUTH_USER_MODEL], null=True),
                      keep_default=False)
        # Check if we have old data to import
        columns = connection.introspection.get_table_description(connection.cursor(), "pootle_app_permissionset")
        if "profile_id" in [f[0] for f in columns] and "pootle_app_pootleprofile" in connection.introspection.table_names():
            print("Migrating PermissionSet Profile data to User. This may take a while.")
            db.execute("""UPDATE pootle_app_permissionset SET user_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                          WHERE pootle_app_pootleprofile.id = pootle_app_permissionset.profile_id)
                       """)

            # Removing unique constraint on 'PermissionSet', fields ['profile', 'directory']
            db.delete_unique(u'pootle_app_permissionset', ['profile_id', 'directory_id'])

            # Deleting field 'PermissionSet.profile'
            db.delete_column(u'pootle_app_permissionset', 'profile_id')

        # Set the new user_id column to NOT NULL. Doesn't work in sqlite.
        if db.backend_name == "postgresql":
            db.execute("ALTER TABLE pootle_app_permissionset ALTER COLUMN user_id SET NOT NULL")
        elif db.backend_name == "mysql":
            # disgusting...
            db.execute("ALTER TABLE pootle_app_permissionset MODIFY user_id INTEGER NOT NULL")

        # Adding unique constraint on 'PermissionSet', fields ['user', 'directory']
        db.create_unique(u'pootle_app_permissionset', ['user_id', 'directory_id'])

    def backwards(self, orm):
        # Removing unique constraint on 'PermissionSet', fields ['user', 'directory']
        db.delete_unique(u'pootle_app_permissionset', ['user_id', 'directory_id'])

        # Adding field 'PermissionSet.profile'. FIXME: Lossy
        db.add_column(u'pootle_app_permissionset', 'profile',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['accounts.User']),
                      keep_default=False)

        # Adding unique constraint on 'PermissionSet', fields ['profile', 'directory']
        db.create_unique(u'pootle_app_permissionset', ['profile_id', 'directory_id'])

        # Deleting field 'PermissionSet.user'
        db.delete_column(u'pootle_app_permissionset', 'user_id')

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'pootle_app.directory': {
            'Meta': {'ordering': "['name']", 'object_name': 'Directory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_dirs'", 'null': 'True', 'to': "orm['pootle_app.Directory']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'pootle_app.permissionset': {
            'Meta': {'unique_together': "(('profile', 'directory'),)", 'object_name': 'PermissionSet'},
            'directory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permission_sets'", 'to': "orm['pootle_app.Directory']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'negative_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'permission_sets_negative'", 'symmetrical': 'False', 'to': u"orm['auth.Permission']"}),
            'positive_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'related_name': "'permission_sets_positive'", 'symmetrical': 'False', 'to': u"orm['auth.Permission']"}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.User']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['%s']" % (AUTH_USER_MODEL), 'null': 'True'})
        },
        'pootle_app.pootleconfig': {
            'Meta': {'object_name': 'PootleConfig'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ptl_build': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ttk_build': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'pootle_app.pootlesite': {
            'Meta': {'object_name': 'PootleSite'},
            'description': ('pootle.core.markup.fields.MarkupField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sites.Site']", 'unique': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'default': "'Pootle Demo'", 'max_length': '50'})
        },
        'pootle_app.suggestion': {
            'Meta': {'object_name': 'Suggestion'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'review_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviewer'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '16', 'db_index': 'True'}),
            'suggester': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggester'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_translationproject.TranslationProject']"}),
            'unit': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
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
            'failing_critical_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'fuzzy_wordcount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_language.Language']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_project.Project']"}),
            'real_path': ('django.db.models.fields.FilePathField', [], {'max_length': '100'}),
            'suggestion_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'total_wordcount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'translated_wordcount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['pootle_app']
