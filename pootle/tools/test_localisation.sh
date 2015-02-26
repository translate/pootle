#!/bin/bash

basedir=$(dirname $0)/../..

if [ $# -lt 1 ]; then
	echo "$(basename $0) [--pot] <lang> [style (default is xxx)]"
	exit 1
fi

if [[ $1 == "--pot" ]]; then
	pot="yes"
	shift
fi

lang=$1
style=${2-xxx}

cd $basedir

[[ $pot ]] && make pot

cd pootle
mkdir -p locale/$lang
podebug --rewrite=$style --progress=none locale/templates/pootle.pot locale/$lang/pootle.po
podebug --rewrite=$style --progress=none locale/templates/pootle_js.pot locale/$lang/pootle_js.po

for pofile in locale/$lang/pootle.po locale/$lang/pootle_js.po
do
	[[ $(egrep "INTEGER" $pofile) ]] || sed -i .bak '/^"Content-Transfer-Encoding: /a\
"Plural-Forms: nplurals=2; plural=(n!=1);\\n"
' $pofile
	sed -i .bak "s/INTEGER/2/g;s/EXPRESSION/(n!=1)/g" $pofile
done

cd ..
./setup.py build_mo --lang=$lang
