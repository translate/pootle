#!/bin/bash

script_location=$(dirname $0)

cd $script_location/../locale

linguas=LINGUAS

default_target=80
target=${1:-$default_target}
shift
required_langs=$*

for lang in $(ls)
do
	if [ -d "$lang" -a "$lang" != "templates" -a ! -L "$lang" ]; then
        completeness=$(pocount --no-color $(find $lang -name "*.po" -type f) | egrep "^Translated" | cut -d"(" -f2- | cut -d")" -f1 | sed "s/%//" | tail -1)
		if [[ $completeness -ge $target ]]; then
			echo $lang
        elif [[ $required_langs =~ (^|[[:space:]])$lang($|[[:space:]]) ]]; then
            echo $lang
            >&2 echo "$lang included as a default language (only ${completeness}% complete)"
		fi
	fi
done > $linguas

if [[ $(which git) ]]; then
    git diff --exit-code $linguas
fi
