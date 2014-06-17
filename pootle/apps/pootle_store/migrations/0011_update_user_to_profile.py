# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.db import connection, models


class Migration(SchemaMigration):

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

            print("Starting migration from Profile to User.")
            print("This may take anywhere between a few minutes to several hours, depending on the size of your projects.")

            print("Migrating Suggestion.user (Step 1 of 5)")
            db.execute("""UPDATE pootle_store_suggestion SET user_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_store_suggestion.user_id)
                       """)

            print("Migrating Suggestion.reviewer (Step 2 of 5)")
            db.execute("""UPDATE pootle_store_suggestion SET reviewer_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_store_suggestion.reviewer_id)
                       """)

            print("Migrating TMUnit.submitted_by (Step 3 of 5)")
            db.execute("""UPDATE pootle_store_tmunit SET submitted_by_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_store_tmunit.submitted_by_id)
                       """)

            print("Migrating Unit.submitted_by (Step 4 of 5)")
            db.execute("""UPDATE pootle_store_unit SET submitted_by_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_store_unit.submitted_by_id)
                       """)

            print("Migrating Unit.commented_by (Step 5 of 5)")
            db.execute("""UPDATE pootle_store_unit SET commented_by_id =
                          (select pootle_app_pootleprofile.user_id FROM pootle_app_pootleprofile
                           WHERE pootle_app_pootleprofile.id = pootle_store_unit.commented_by_id)
                       """)

    def backwards(self, orm):
        raise NotImplementedError

    complete_apps = ["pootle_store"]
