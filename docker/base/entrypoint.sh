#!/bin/bash

# If local_user_id is set usermod to this user

POOTLE_ID=$(id -u pootle)

if [[ ( ! -z ${LOCAL_USER_ID:+x} ) && ( "$LOCAL_USER_ID" != "$POOTLE_ID" ) ]]; then
    echo "Starting with UID : $LOCAL_USER_ID";
    usermod -o -u $LOCAL_USER_ID pootle
fi

export HOME=/home/pootle
exec gosu pootle "$@"
