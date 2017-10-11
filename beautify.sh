#!/bin/sh

if [ $# -eq 0 ] ; then
    for f in static/js/*.js ; do
	js-beautify -tnr --brace-style=end-expand $f
    done
else
    for f in $* ; do
	js-beautify -tnr --brace-style=end-expand $f
    done
fi

