#!/bin/bash

dups=$(cat requirements/*.txt | egrep -v "^#|^$|^-r" | cut -d">" -f1 | cut -d "<" -f1 | cut -d'!' -f1 | cut -d"=" -f1 | sort | uniq -d)

for dup in $dups
do
    egrep $dup requirements/*.txt
done
