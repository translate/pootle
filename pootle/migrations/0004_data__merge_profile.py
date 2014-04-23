# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class Migration(DataMigration):
    depends_on = (
        ("pootle_profile", "0005_auto__add_field_pootleprofile_review_rate"),
        ("evernote_auth", "0002_data__adjust_pks"),
        ("staticpages", "0012_data__adjust_pks"),
    )

    def forwards(self, orm):
        """Merge PootleProfile information into the User model."""
        # As a safety measure, increase user IDs not to produce clashes
        # later when updating them with existing PootleProfile IDs
        offset = 100000
        for user in orm['pootle.User'].objects.iterator():
            # It's necessary to use South's DB API to update primary keys,
            # otherwise Django will perform an INSERT even if
            # `save(force_update=True)` is used
            tmp_user_id = user.id + offset
            db.execute('UPDATE pootle_user SET id=%s WHERE id=%s',
                       params=[tmp_user_id, user.id])

        for user in orm['pootle.User'].objects.order_by('-id').iterator():
            old_user_id = user.id - offset

            try:
                profile = orm['pootle_profile.PootleProfile'].objects.get(
                    user__id=old_user_id,
                )
            except ObjectDoesNotExist:
                continue

            new_user_id = profile.id
            db.execute('UPDATE pootle_user SET id=%s WHERE id=%s',
                       params=[new_user_id, user.id])

            # ID changed: refetch user object before updating it
            user = orm['pootle.User'].objects.get(id=new_user_id)

            # Migrate field data to the user this profile points to
            user.unit_rows = profile.unit_rows
            user.rate = profile.rate
            user.review_rate = profile.review_rate
            user.score = profile.score

            for alt_src_lang in profile.alt_src_langs.all():
                user.alt_src_langs.add(alt_src_lang)

            user.save(force_update=True)

    def backwards(self, orm):
        """Write your backwards methods here."""

    models = {
        'pootle.user': {
            'Meta': {'object_name': 'User'},
            'alt_src_langs': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'to': u"orm['pootle_language.Language']", 'symmetrical': 'False', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'rate': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'review_rate': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'score': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'unit_rows': ('django.db.models.fields.SmallIntegerField', [], {'default': '9'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'pootle_app.directory': {
            'Meta': {'ordering': "['name']", 'object_name': 'Directory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_dirs'", 'null': 'True', 'to': "orm['pootle_app.Directory']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'pootle_language.language': {
            'Meta': {'ordering': "['code']", 'object_name': 'Language', 'db_table': "'pootle_app_language'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nplurals': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'pluralequation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'specialchars': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'pootle_profile.pootleprofile': {
            'Meta': {'object_name': 'PootleProfile', 'db_table': "'pootle_app_pootleprofile'"},
            'alt_src_langs': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_alt_src_langs'", 'blank': 'True', 'db_index': 'True', 'to': u"orm['pootle_language.Language']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_height': ('django.db.models.fields.SmallIntegerField', [], {'default': '5'}),
            'rate': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'review_rate': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'score': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'ui_lang': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'unit_rows': ('django.db.models.fields.SmallIntegerField', [], {'default': '9'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['pootle_profile', 'pootle']
    symmetrical = True
