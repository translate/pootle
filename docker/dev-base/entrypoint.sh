#!/bin/bash

# Add local user
# Either use the LOCAL_USER_ID if passed in at runtime or
# fallback

USER_ID=${LOCAL_USER_ID:$UID}

echo "Starting with UID : $USER_ID"
usermod -o -u $USER_ID pootle
export HOME=/home/pootle
exec gosu pootle "$@"
