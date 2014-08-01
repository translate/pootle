# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.db import connection, models


class Migration(SchemaMigration):
    depends_on = (
        ("accounts", "0001_initial"),
    )

    no_dry_run = True

    def forwards(self, orm):
        # First we check whether the migration is needed.
        profiles_table = "pootle_app_pootleprofile"
        if profiles_table in connection.introspection.table_names():
            # Here we need to:
            # 1. Update all Suggestion.user fields
            # 2. Update all Suggestion.reviewer fields
            # 3. Update all TMUnit.submitted_by fields
            # 4. Update all Unit.submitted_by fields
            # 5. Update all Unit.commented_by fields

            def clean_constraints(t1, c1, t2, c2):
                # Workaround for http://south.aeracode.org/ticket/775
                if db.backend_name != "sqlite3":
                    try:
                        db.delete_foreign_key(t1, c1)
                        db.execute(db.foreign_key_sql(t1, c1, t2, c2))
                    except ValueError as e:
                        print("Warning: Could not clean up constraints (this may be harmless): %s" % (e))

            print("Starting migration from Profile to User.")
            print("This may take anywhere between a few minutes to several hours, depending on the size of your projects.")

            print("Migrating Suggestion.user (Step 1 of 6)")
            db.execute("""UPDATE pootle_store_suggestion SET user_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_store_suggestion.user_id)
                       """)
            clean_constraints("pootle_store_suggestion", "user_id", "accounts_user", "id")

            print("Migrating Suggestion.reviewer (Step 2 of 6)")
            db.execute("""UPDATE pootle_store_suggestion SET reviewer_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_store_suggestion.reviewer_id)
                       """)
            clean_constraints("pootle_store_suggestion", "reviewer_id", "accounts_user", "id")

            print("Migrating TMUnit.submitted_by (Step 3 of 6)")
            db.execute("""UPDATE pootle_store_tmunit SET submitted_by_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_store_tmunit.submitted_by_id)
                       """)
            clean_constraints("pootle_store_tmunit", "submitted_by_id", "accounts_user", "id")

            print("Migrating Unit.submitted_by (Step 4 of 6)")
            db.execute("""UPDATE pootle_store_unit SET submitted_by_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_store_unit.submitted_by_id)
                       """)
            clean_constraints("pootle_store_unit", "submitted_by_id", "accounts_user", "id")

            print("Migrating Unit.commented_by (Step 5 of 6)")
            db.execute("""UPDATE pootle_store_unit SET commented_by_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_store_unit.commented_by_id)
                       """)
            clean_constraints("pootle_store_unit", "commented_by_id", "accounts_user", "id")

            print("Migrating Submission.submitter_id (Step 6 of 6)")
            db.execute("""UPDATE pootle_app_submission SET submitter_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_app_submission.submitter_id)
                       """)
            clean_constraints("pootle_app_submission", "submitter_id", "accounts_user", "id")

    def backwards(self, orm):
        raise NotImplementedError

    complete_apps = ["pootle_store"]
