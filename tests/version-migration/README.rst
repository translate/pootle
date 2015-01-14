Version Migration Testing
=========================

Purpose
-------
To catch migration errors across versions and databases as we make changes.
Thus preventing us releasing versions of Pootle that cannot migrate wasting
time assisting Pootle users one by one.  Rather catch the issue early.

We do this by automatically testing migrations from various old versions of
Pootle to the version being tested.

How it works
------------
Mostly this will be tested on Travis but you can test locally.

1. migrate.sh when run will read ``$DATABASE_ENGINE`` or read the first option
   and run against that database.  Thus ``./migrate sqlite`` will run the tests
   for sqlite.
2. All database dumps in ``data/`` for the database under test are found.
3. For each dump we:

   1. Load the dump into the database.  We now have a Pootle database at the
      older install state.
   2. Migrate to the latest version.


Coding the migrations
---------------------
The migrations follow the instructions we give users in the Pootle docs as we
need to test following the instructions that we give.  Instructions are given
for each version from which we migrate.

Creating new database dumps
---------------------------
To create a database dump for an older Pootle version you will need to:

1. Install Pootle for that older version, preferably in a virtualenv
2. Create a Pootle database if needed (MySQL, Postgress)
3. Setup the Pootle configuration:

   1. Setup the correct database config
   2. Enable memcached (to prevent any issues related to database cache tables)

4. Run the correct Pootle setup commands
5. Run Pootle such that it can import and configure things in older versions.
   Running refresh_stats and such can be helpful to make sure Pootle is in
   running order, not just post install state.
6. Dump the database to ``data/[description]-$engine-$pootle_versions.sql``
7. Commit to Git and make sure any needed migration instructions are in place.
