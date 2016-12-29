#!/bin/bash

# Default to MySQL
: ${DATABASE:=mysql}
: ${INSTALL_DIR:=/pootle}
: ${CONFIG_DIR:=/config}

if [[ "$DATABASE" == "mysql" ]]; then
    : ${POOTLE_DB_USER:=${DBSERVER_ENV_MYSQL_USER:-root}}
    : ${POOTLE_DB_PASSWORD:=$DBSERVER_ENV_MYSQL_PASSWORD}
    if [ "$POOTLE_DB_USER" = 'root' ]; then
        : ${POOTLE_DB_PASSWORD:$DBSERVER_ENV_MYSQL_ROOT_PASSWORD}
    fi
    # Default to "POOTLE"
    : ${POOTLE_DB_NAME:=${DBSERVER_ENV_MYSQL_DATABASE:-pootledb}}
elif [[ "$DATABASE" == "postgresql" ]]; then
    echo 'PostgreSQL was chosen as database backend.'
    echo >&2 'ERROR: PostgreSQL support not implemented yet in Docker image.'
    exit 2
elif [[ "$DATABASE" == "sqlite3" ]]; then
    echo 'SQLite3 was chosen as database backend.'
    echo >&2 'ERROR: SQLite3 support not implemented yet in Docker image.'
    exit 2
fi

if [ -z "$POOTLE_DB_PASSWORD" ]; then
    echo >&2 'error: missing required POOTLE_DB_PASSWORD environment variable'
    echo >&2 '  Did you forget to -e POOTLE_DB_PASSWORD=... ?'
    echo >&2
    echo >&2 '  (Also of interest might be POOTLE_DB_USER and POOTLE_DB_NAME.)'
    exit 1
fi

: "${POOTLE_DB_HOSTNAME:=dbserver}"
: "${DOMAIN:=""}" # By defaulting this empty we set ALLOWED_HOSTS to '*', thus avoiding "Bad request 400" when accessed form non "localhost"

CONFIG_FILE="$CONFIG_DIR/pootle.conf"

if [ ! -f $CONFIG_FILE ]; then
    cd $INSTALL_DIR \
    && . bin/activate || exit 3
    echo "Creating initial Pootle configuration..."
    pootle init --config $CONFIG_FILE \
        --db $DATABASE \
        --db-name $POOTLE_DB_NAME \
        --db-user $POOTLE_DB_USER \
        --db-host $POOTLE_DB_HOSTNAME || exit 3
    echo "Created initial Pootle configuration. See documentation for help on customising the settings: http://docs.translatehouse.org/projects/pootle/en/stable-2.7.6/server/settings.html"
    # exit virtualenv
    deactivate || exit 3
fi

# configure Redis

# handle upgrade scenario
    # pootle migrate

# populate fresh install database
    # pootle initdb
