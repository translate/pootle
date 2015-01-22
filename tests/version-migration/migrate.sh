#!/bin/bash

user_supplied_db=$1
# Use Travis setup i.e. settings/91-travis.conf
export TRAVIS=1
export DATABASE_BACKEND=${DATABASE_BACKEND:=$user_supplied_db}
basedir=$(dirname "$0")
datadir=$(readlink -f $basedir/data)
dbname=pootle
dbuser_postgres=postgres
dbuser_mysql=travis

cd "$basedir/../.."

if [[ ! $DATABASE_BACKEND ]]; then
	echo "Error: set DATABASE_BACKEND or supply database backend as first parameter"
	exit 1
fi

function load_database {
	local database_dump=$1
	echo "Loading $database_dump into $DATABASE_BACKEND"
	case $DATABASE_BACKEND in
		mysql)
			mysql -u $dbuser_mysql <<-EOMy
			drop database $dbname;
			create database $dbname CHARACTER SET utf8 COLLATE utf8_general_ci;
			EOMy
			mysql -u $dbuser_mysql $dbname < $database_dump
			;;
		postgres)
			psql -U $dbuser_postgres -d $dbname -f $database_dump
			;;
		sqlite)
			if [[ "$user_supplied_db" ]]; then
				read -p "Deleting 'pootle/dbs/${dbname}_travis.db' Do you wish to proceed?" -n1 answer
			        echo
				if [ "$answer" != "y" ]; then
					exit
				fi
			fi
			rm pootle/dbs/${dbname}_travis.db
			sqlite3 pootle/dbs/${dbname}_travis.db < $database_dump
			;;
		*)
			echo "Error: $DATABASE_BACKEND is unkonwn"
			exit 1
			;;
	esac
}

function migrate_database {
	pootle_versions=$1
	echo "Migrating $pootle_version to latest on $DATABASE_BACKEND"
	case $pootle_version in
		2.1.6)
			echo "Not implemented"
			exit 1
			;;
		2.5.0)
			echo "Migrating using $pootle_version rules"
			./manage.py setup --traceback -v0
			;;
		2.5.1)
			echo "Migrating using $pootle_version rules"
			./manage.py setup --traceback -v0
			;;
		*)
			echo "Error: missing rules for migrating from $pootle_version"
			exit 1
			;;
	esac
}

for database_dump in $(find $datadir -name "*-$DATABASE_BACKEND-*.sql")
do
	pootle_version=$(echo $database_dump | sed "s/.*-\([^-]*\)\.sql/\1/")
	load_database $database_dump
	migrate_database $pootle_version
	# TODO actually run the server
done
