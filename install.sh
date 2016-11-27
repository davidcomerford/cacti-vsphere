#!/bin/bash

CACTIPATH="/var/www/html/cacti"

function doTheThings {
   cp -v cacti-vpshere.py $CACTIPATH/scripts/
   cp -v vcenters.conf $CACTIPATH/scripts/
}

echo $CACTIPATH

echo "Does this Cacti path look Ok?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) doTheThings; break;;
        No ) echo "Fix the path variable in $0 " ; exit;;
    esac
done
