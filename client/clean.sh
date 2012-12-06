#!/bin/sh

for i in `find ./ -iname "*.pyc"`;
do
	rm $i;
done

for i in `find ./ -iname "*.*~"`;
do
        rm $i;
done
