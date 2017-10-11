#!/bin/sh

if [ $# -eq 0 ] ; then
	js-beautify -tnr --brace-style=end-expand static/js/*.js
else
	js-beautify -tnr --brace-style=end-expand $*
fi

