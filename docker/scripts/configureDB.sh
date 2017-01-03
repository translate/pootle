#!/bin/bash

DB_INIT_PARAMS="--db $DATABASE"

if [[ "$DATABASE" == "mysql" ]]; then
    : ${POOTLE_DB_USER:=${DBSERVER_ENV_MYSQL_USER:-root}}
    : ${POOTLE_DB_PASSWORD:=$DBSERVER_ENV_MYSQL_PASSWORD}
    if [ "$POOTLE_DB_USER" = 'root' ]; then
        : ${POOTLE_DB_PASSWORD:$DBSERVER_ENV_MYSQL_ROOT_PASSWORD}
    fi
    # Default to "POOTLE"
    : ${POOTLE_DB_NAME:=${DBSERVER_ENV_MYSQL_DATABASE:-pootledb}}

    if [ -z "$POOTLE_DB_PASSWORD" ]; then
        echo >&2 'error: missing required POOTLE_DB_PASSWORD environment variable'
        echo >&2 '  Did you forget to -e POOTLE_DB_PASSWORD=... ?'
        echo >&2
        echo >&2 '  (Also of interest might be POOTLE_DB_USER and POOTLE_DB_NAME.)'
        exit 1
    fi

    : "${POOTLE_DB_HOSTNAME:=dbserver}"

    DB_INIT_PARAMS="$DB_INIT_PARAMS \
        --db-name $POOTLE_DB_NAME \
        --db-user $POOTLE_DB_USER \
        --db-host $POOTLE_DB_HOSTNAME"

elif [[ "$DATABASE" == "postgresql" ]]; then
    echo 'PostgreSQL was chosen as database backend.'
    echo >&2 'ERROR: PostgreSQL support not implemented yet in Docker image.'
    exit 2
elif [[ "$DATABASE" == "sqlite" ]]; then
    echo 'SQLite3 was chosen as database backend.'
fi
