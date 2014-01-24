#!/bin/bash

script_location=$(dirname $0)

cd $script_location/../locale

default_target=80
target=${1:-$default_target}

for lang in $(ls)
do
	if [ -d "$lang" -a "$lang" != "templates" ]; then
		completeness=$(pocount  $(find $lang -name "*.po") | egrep "^translated" | cut -d"(" -f2- | cut -d")" -f1 | sed "s/%//" | tail -1)
		if [ $completeness -ge $target ]; then
			echo $lang
		fi
	fi
done
