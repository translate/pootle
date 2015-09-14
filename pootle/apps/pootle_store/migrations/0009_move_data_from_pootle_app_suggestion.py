# -*- coding: utf-8 -*-
import datetime
import logging
from hashlib import md5
from itertools import groupby

from south.db import db
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db.utils import IntegrityError

from south.v2 import DataMigration


_debug = True


class Migration(DataMigration):

    depends_on = (
        ("pootle_statistics", "0003_auto__add_field_submission_suggestion"),
        ("pootle_translationproject", "0006_auto__add_field_translationproject_failing_critical_count"),
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
            for ss in unit.suggestion_set.filter(user__isnull=False):
                # Remove the user for suggestions referring to non-existing
                # users. This can only happen if constraints are not enforced,
                # for example when using MyISAM.
                # Note that this suggestions will be assigned to 'nobody' on
                # migration 0022.
                try:
                    orm['accounts.User'].objects.get(id=ss.user_id)
                except ObjectDoesNotExist:
                    ss.user = None
                    ss.save()

            store_suggestions = unit.suggestion_set.filter(user__isnull=False).order_by('user')
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
                        sugg.translation_project = pas.translation_project
                        sugg.save()

                        logging.debug("pas %d copied and will be deleted" % pas.id)
                        stats['ONE_TO_ONE_COPY'] += 1
                        pas.delete()

                    else:
                        # there should be no such data in the database
                        logging.debug("%d pending suggestions by %d for %d" % (len_ss, user_id, unit.id))
                        stats['MANY_TO_MANY_COPY'] += 1

                elif len_ss > len_app_pending_suggestions:
                    logging.debug("%d pss > %d pas for unit %d" % (len_ss, len_app_pending_suggestions, unit.id))
                    if len_app_pending_suggestions > 0:
                        stats['PAS_LESS_THAN_PSS'] += 1
                    else:
                        stats['NO_PAS_FOR_PSS'] += 1

                    app_pending_suggestions.delete()

                else:
                    # there should be no such data in the database
                    logging.debug("%d pss < %d pas for %d" % (len_ss, len_app_pending_suggestions, unit.id))
                    stats['PSS_LESS_THAN_PAS'] += 1

        # all pootle_app_suggestions corresponding to pootle_store_suggestions have been already deleted

        existing_keys = list(orm['pootle_store.Suggestion'].objects.values_list('unit_id', 'target_hash'))

        for pas in orm['pootle_app.Suggestion'].objects.all():
            try:
                # unit isn't deleted
                unit = orm['pootle_store.Unit'].objects.get(id=pas.unit)

                if pas.state == 'accepted':
                    try:
                        # to restore suggestion by submission
                        sub = orm['pootle_statistics.Submission'].objects.get(unit=unit, from_suggestion=pas)
                        target = u"%s" % sub.new_value

                        target_hash = md5(target.encode("utf-8")).hexdigest()
                        if (unit.pk, target_hash) in existing_keys:
                            # Do not insert duplicate suggestions.
                            logging.debug("failed to create duplicated suggestion from pas %d and sub %d" % (pas.id, sub.id))
                            sub.delete()
                            stats['DUPLICATED_SUG'] += 1
                            continue
                        existing_keys.append((unit.pk, target_hash))

                        sugg = {
                            "target_hash": target_hash,
                            "target_f": target,
                            "creation_time": pas.creation_time,
                            "review_time": sub.creation_time,
                            "user_id": pas.suggester_id,
                            "reviewer_id": pas.reviewer_id,
                            "unit_id": unit.pk,
                            "state": pas.state, #accepted
                            "translator_comment_f": None,
                            "translation_project_id": sub.translation_project_id,
                        }

                        try:
                            keys = [
                                "target_hash", "target_f", "creation_time", "review_time",
                                "user_id", "reviewer_id", "unit_id", "state",
                                "translator_comment_f", "translation_project_id"
                            ]
                            values = [sugg[k] for k in keys]
                            db.execute("""
                                INSERT INTO pootle_store_suggestion
                                (target_hash, target_f, creation_time, review_time,
                                 user_id, reviewer_id, unit_id, state,
                                 translator_comment_f, translation_project_id)
                                VALUES
                                (%s, %s, %s, %s,
                                 %s, %s, %s, %s,
                                 %s, %s)""", values)
                            sub.suggestion_id = connection.cursor().lastrowid
                            sub.save()

                            logging.debug("suggestion created from pas %d and sub %d" % (pas.id, sub.id))
                            stats['SUG_CREATED_FROM_SUB'] += 1

                        except IntegrityError:
                            logging.debug("failed to create duplicated suggestion from pas %d and sub %d" % (pas.id, sub.id))

                            sub.delete()
                            stats['DUPLICATED_SUG'] += 1

                    except orm['pootle_statistics.Submission'].DoesNotExist:
                        logging.debug('No submission found for pas %d' % pas.id)
                        stats['NO_SUB_FOR_PAS'] += 1

                elif pas.state == 'pending':
                    logging.debug('No suggestion found for pending pas %d' % pas.id)
                    stats['NO_PSS_FOR_PENDING_PAS'] += 1
                else:
                    logging.debug('Delete rejected pas %d' % pas.id)
                    stats['DEL_REJECTED_PAS'] += 1

            except orm['pootle_store.Unit'].DoesNotExist:
                logging.debug('no unit for %d' % pas.id)
                stats['NO_UNIT_FOR_PAS'] += 1

            pas.delete()

        logging.info("%s" % stats)

    def backwards(self, orm):
        pass

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
        u'accounts.user': {
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
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.User']", 'null': 'True'})
        },
        'pootle_app.suggestion': {
            'Meta': {'object_name': 'Suggestion'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'review_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviewer'", 'null': 'True', 'to': "orm['accounts.User']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '16', 'db_index': 'True'}),
            'suggester': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggester'", 'null': 'True', 'to': "orm['accounts.User']"}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pootle_translationproject.TranslationProject']"}),
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
        u'pootle_statistics.submission': {
            'Meta': {'ordering': "['creation_time']", 'object_name': 'Submission', 'db_table': "'pootle_app_submission'"},
            'check': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.QualityCheck']", 'null': 'True', 'blank': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'field': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'from_suggestion': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pootle_app.Suggestion']", 'unique': 'True', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_value': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'old_value': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.User']", 'null': 'True'}),
            'suggestion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Suggestion']", 'null': 'True', 'blank': 'True'}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_translationproject.TranslationProject']"}),
            'type': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Unit']", 'null': 'True', 'blank': 'True'})
        },
        u'pootle_store.qualitycheck': {
            'Meta': {'object_name': 'QualityCheck'},
            'category': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'false_positive': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Unit']"})
        },
        u'pootle_store.store': {
            'Meta': {'ordering': "['pootle_path']", 'unique_together': "(('parent', 'name'),)", 'object_name': 'Store'},
            'failing_critical_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'file': ('pootle_store.fields.TranslationStoreField', [], {'max_length': '255', 'db_index': 'True'}),
            'fuzzy_wordcount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child_stores'", 'to': "orm['pootle_app.Directory']"}),
            'pootle_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'suggestion_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'sync_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1, 1, 1, 0, 0)'}),
            'total_wordcount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'translated_wordcount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stores'", 'to': u"orm['pootle_translationproject.TranslationProject']"})
        },
        u'pootle_store.suggestion': {
            'Meta': {'unique_together': "(('unit', 'target_hash'),)", 'object_name': 'Suggestion'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'review_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviews'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '16', 'db_index': 'True'}),
            'target_f': ('pootle_store.fields.MultiStringField', [], {}),
            'target_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'translation_project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggestions'", 'null': 'True', 'to': u"orm['pootle_translationproject.TranslationProject']"}),
            'translator_comment_f': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Unit']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggestions'", 'null': 'True', 'to': u"orm['accounts.User']"})
        },
        u'pootle_store.tmunit': {
            'Meta': {'object_name': 'TMUnit'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_project.Project']"}),
            'source_f': ('pootle_store.fields.MultiStringField', [], {'null': 'True'}),
            'source_lang': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tmunit_source_lang'", 'to': u"orm['pootle_language.Language']"}),
            'source_length': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tmunit_submitted_by'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'submitted_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'target_f': ('pootle_store.fields.MultiStringField', [], {'null': 'True'}),
            'target_lang': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tmunit_target_lang'", 'to': u"orm['pootle_language.Language']"}),
            'target_length': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Unit']"})
        },
        u'pootle_store.unit': {
            'Meta': {'ordering': "['store', 'index']", 'unique_together': "(('store', 'unitid_hash'),)", 'object_name': 'Unit'},
            'commented_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'commented'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'commented_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'context': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'developer_comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'locations': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source_f': ('pootle_store.fields.MultiStringField', [], {'null': 'True'}),
            'source_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'source_length': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'source_wordcount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pootle_store.Store']"}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'submitted_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'target_f': ('pootle_store.fields.MultiStringField', [], {'null': 'True', 'blank': 'True'}),
            'target_length': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'target_wordcount': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'translator_comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'unitid': ('django.db.models.fields.TextField', [], {}),
            'unitid_hash': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'})
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
        }
    }

    complete_apps = ['pootle_app', 'pootle_statistics', 'pootle_store']
    symmetrical = True
