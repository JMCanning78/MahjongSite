#!/bin/sh

if [ $# -eq 0 ] ; then
	js-beautify -tnr --brace-style=end-expand \
		`ls static/js/*.js | fgrep -v .min.js`
else
	js-beautify -tnr --brace-style=end-expand $*
fi

