# -*- coding: utf-8 -*-
import datetime
from hashlib import md5
from itertools import groupby

from django.db.utils import IntegrityError

from south.v2 import DataMigration

from pootle.core.log import log

_debug = True

class Migration(DataMigration):

    depends_on = (
        ("pootle_statistics", "0006_add_another_suggestion_field"),
    )

    def forwards(self, orm):

        stats = {
            'ONE_TO_ONE_COPY': 0,
            'MANY_TO_MANY_COPY': 0, #!!! impossible ?
            'PAS_LESS_THAN_PSS': 0,
            'NO_PAS_FOR_PSS': 0,
            'PSS_LESS_THAN_PAS': 0, #!!! impossible ?
            'SUG_CREATED_FROM_SUB': 0,
            'NO_SUB_FOR_PAS': 0,
            'NO_PSS_FOR_PENDING_PAS': 0,
            'DEL_REJECTED_PAS': 0,
            'NO_UNIT_FOR_PAS': 0,
            'DUPLICATED_SUG': 0,
        }

        # units with suggestions
        units = orm['pootle_store.Unit'].objects.filter(suggestion__isnull=False).distinct()
        for unit in units:
            store_suggestions = unit.suggestion_set.all().order_by('user')
            for user_id, ss in groupby(store_suggestions, lambda x: x.user.id):
                ss = list(ss)
                app_pending_suggestions = orm['pootle_app.Suggestion'].objects \
                    .filter(unit=unit.id, suggester__id=user_id, state='pending')

                len_ss = len(ss)
                len_app_pending_suggestions = len(app_pending_suggestions)

                if len_ss == len_app_pending_suggestions:
                    if len_ss == 1:
                        pas = app_pending_suggestions[0]
                        sugg = ss[0]
                        sugg.state = pas.state # state == pending
                        sugg.creation_time = pas.creation_time
                        sugg.save()

                        log("pas %d copied and will be deleted" % pas.id)
                        stats['ONE_TO_ONE_COPY'] += 1
                        pas.delete()

                    else:
                        # there should be no such data in the database
                        log("%d pending suggestions by %d for %d" % (len_ss, user_id, unit.id))
                        stats['MANY_TO_MANY_COPY'] += 1

                elif len_ss > len_app_pending_suggestions:
                    log("%d pss > %d pas for unit %d" % (len_ss, len_app_pending_suggestions, unit.id))
                    if len_app_pending_suggestions > 0:
                        stats['PAS_LESS_THAN_PSS'] += 1
                    else:
                        stats['NO_PAS_FOR_PSS'] += 1

                    app_pending_suggestions.delete()

                else:
                    # there should be no such data in the database
                    log("%d pss < %d pas for %d" % (len_ss, len_app_pending_suggestions, unit.id))
                    stats['PSS_LESS_THAN_PAS'] += 1

        # all pootle_app_suggestions corresponding to pootle_store_suggestions have been already deleted

        for pas in orm['pootle_app.Suggestion'].objects.all():
            try:
                # unit isn't deleted
                unit = orm['pootle_store.Unit'].objects.get(id=pas.unit)

                if pas.state == 'accepted':
                    try:
                        # to restore suggestion by submission
                        sub = orm['pootle_statistics.Submission'].objects.get(unit=unit, from_suggestion=pas)
                        target = u"%s" % sub.new_value
                        sugg = {
                            'target_f': target,
                            'target_hash': md5(target.encode("utf-8")).hexdigest(),
                            'unit': unit,
                            'user': pas.suggester,
                            'reviewer': pas.reviewer,
                            'review_time': sub.creation_time,
                            'state': pas.state, #accepted
                            'creation_time': None,
                        }
                            
                        try:
                            sugg = orm['pootle_store.Suggestion'].objects.create(**sugg)
                            sub.suggestion = sugg
                            sub.save()

                            log("suggestion created from pas %d and sub %d" % (pas.id, sub.id))
                            stats['SUG_CREATED_FROM_SUB'] += 1

                        except IntegrityError:
                            log("failed to create duplicated suggestion from pas %d and sub %d" % (pas.id, sub.id))

                            sub.delete()
                            stats['DUPLICATED_SUG'] += 1

                    except orm['pootle_statistics.Submission'].DoesNotExist:
                        log('No submission found for pas %d' % pas.id)
                        stats['NO_SUB_FOR_PAS'] += 1

                elif pas.state == 'pending':
                    log('No suggestion found for pending pas %d' % pas.id)
                    stats['NO_PSS_FOR_PENDING_PAS'] += 1
                else:
                    log('Delete rejected pas %d' % pas.id)
                    stats['DEL_REJECTED_PAS'] += 1

            except orm['pootle_store.Unit'].DoesNotExist:
                log('no unit for %d' % pas.id)
                stats['NO_UNIT_FOR_PAS'] += 1

            pas.delete()

        log("%s" % stats)

    def backwards(self, orm):
        pass

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
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
        'pootle_app.permissionset': {
            'Meta': {'unique_together': "(('profile', 'directory'),)", 'object_name': 'PermissionSet'},
            'directory': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permission_sets'", 'to': "orm['pootle_app.Directory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'negative_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'permission_sets_negative'", 'symmetrical': 'False', 'to': "orm['auth.Permission']"}),
            'positive_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'related_name': "'permission_sets_positive'", 'symmetrical': 'False', 'to': "orm['auth.Permission']"}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_profile.PootleProfile']"})
        },
        'pootle_app.revision': {
            'Meta': {'object_name': 'Revision'},
            'counter': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'pootle_app.suggestion': {
            'Meta': {'object_name': 'Suggestion'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'review_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviewer'", 'null': 'True', 'to': "orm['pootle_profile.PootleProfile']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '16', 'db_index': 'True'}),
            'suggester': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggester'", 'null': 'True', 'to': "orm['pootle_profile.PootleProfile']"}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_translationproject.TranslationProject']"}),
            'unit': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        'pootle_language.language': {
            'Meta': {'ordering': "['code']", 'object_name': 'Language', 'db_table': "'pootle_app_language'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nplurals': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'pluralequation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'specialchars': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'pootle_profile.pootleprofile': {
            'Meta': {'object_name': 'PootleProfile', 'db_table': "'pootle_app_pootleprofile'"},
            'alt_src_langs': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_alt_src_langs'", 'blank': 'True', 'db_index': 'True', 'to': "orm['pootle_language.Language']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_height': ('django.db.models.fields.SmallIntegerField', [], {'default': '5'}),
            'ui_lang': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'unit_rows': ('django.db.models.fields.SmallIntegerField', [], {'default': '9'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'pootle_project.project': {
            'Meta': {'ordering': "['code']", 'object_name': 'Project', 'db_table': "'pootle_app_project'"},
            'checkstyle': ('django.db.models.fields.CharField', [], {'default': "'standard'", 'max_length': '50'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignoredfiles': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'localfiletype': ('django.db.models.fields.CharField', [], {'default': "'po'", 'max_length': '50'}),
            'screenshot_search_prefix': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'source_language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_language.Language']"}),
            'treestyle': ('django.db.models.fields.CharField', [], {'default': "'auto'", 'max_length': '20'})
        },
        'pootle_statistics.submission': {
            'Meta': {'ordering': "['creation_time']", 'object_name': 'Submission', 'db_table': "'pootle_app_submission'"},
            'check': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_store.QualityCheck']", 'null': 'True', 'blank': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'field': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'from_suggestion': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Suggestion']", 'unique': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_value': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'old_value': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_store.Store']", 'null': 'True', 'blank': 'True'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_profile.PootleProfile']", 'null': 'True'}),
            'suggestion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_store.Suggestion']", 'null': 'True', 'blank': 'True'}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_translationproject.TranslationProject']"}),
            'type': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_store.Unit']", 'null': 'True', 'blank': 'True'})
        },
        'pootle_store.qualitycheck': {
            'Meta': {'object_name': 'QualityCheck'},
            'category': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'false_positive': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_store.Unit']"})
        },
        'pootle_store.store': {
            'Meta': {'ordering': "['pootle_path']", 'unique_together': "(('parent', 'name'),)", 'object_name': 'Store'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'file': ('pootle_store.fields.TranslationStoreField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync_revision': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_stores'", 'to': "orm['pootle_app.Directory']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'sync_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1, 1, 1, 0, 0)'}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stores'", 'to': "orm['pootle_translationproject.TranslationProject']"})
        },
        'pootle_store.suggestion': {
            'Meta': {'unique_together': "(('unit', 'target_hash'),)", 'object_name': 'Suggestion'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'review_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviews'", 'null': 'True', 'to': "orm['pootle_profile.PootleProfile']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '16', 'db_index': 'True'}),
            'target_f': ('pootle_store.fields.MultiStringField', [], {}),
            'target_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'translator_comment_f': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_store.Unit']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggestions'", 'null': 'True', 'to': "orm['pootle_profile.PootleProfile']"})
        },
        'pootle_store.unit': {
            'Meta': {'ordering': "['store', 'index']", 'unique_together': "(('store', 'unitid_hash'),)", 'object_name': 'Unit'},
            'commented_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'commented'", 'null': 'True', 'to': "orm['pootle_profile.PootleProfile']"}),
            'commented_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'context': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'developer_comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'locations': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True', 'blank': 'True'}),
            'source_f': ('pootle_store.fields.MultiStringField', [], {'null': 'True'}),
            'source_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'source_length': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'source_wordcount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_store.Store']"}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted'", 'null': 'True', 'to': "orm['pootle_profile.PootleProfile']"}),
            'submitted_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'target_f': ('pootle_store.fields.MultiStringField', [], {'null': 'True', 'blank': 'True'}),
            'target_length': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'target_wordcount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'translator_comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'unitid': ('django.db.models.fields.TextField', [], {}),
            'unitid_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'})
        },
        'pootle_translationproject.translationproject': {
            'Meta': {'unique_together': "(('language', 'project'),)", 'object_name': 'TranslationProject', 'db_table': "'pootle_app_translationproject'"},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'directory': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Directory']", 'unique': 'True'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_language.Language']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_project.Project']"}),
            'real_path': ('django.db.models.fields.FilePathField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['pootle_app', 'pootle_statistics', 'pootle_store']
    symmetrical = True
