#!/bin/bash

for image in $(ls ../pootle/static/images/)
do
	name=$(echo $image | sed "s/\..*$//" )
	echo ".. |icon:$name| image:: /../pootle/static/images/$image"
	echo "          :alt: $(echo $name | sed 's/-/ /') icon"
	echo
done > icons.txt
